import base64
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import server.main as main
from backend.ai.llm import cloudflare_provider
from backend.ai.llm.cloudflare_provider import CloudflareImageProvider
from backend.database.db_store import get_db


async def unused_db():
    yield object()


@pytest.fixture
def client():
    user = SimpleNamespace(id=uuid4(), full_name="Alex Morgan", email="alex@example.com")

    async def current_user():
        return user

    main.app.dependency_overrides[get_db] = unused_db
    main.app.dependency_overrides[main.get_current_user] = current_user
    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client, user
    main.app.dependency_overrides.clear()


def test_generate_images_uses_frontend_request_shape(client, monkeypatch):
    test_client, user = client
    project_id, draft_id, request_key = uuid4(), uuid4(), uuid4()
    created_at = datetime.now(UTC)
    image = SimpleNamespace(
        id=uuid4(),
        draft_id=draft_id,
        project_id=project_id,
        style="Editorial",
        image_count=1,
        aspect_ratio="4:5",
        prompt="A bright editorial composition",
        url="/generated-images/example.jpg",
        created_at=created_at,
    )

    async def fake_save(
        requested_draft_id,
        requested_project_id,
        user_id,
        db,
        style,
        image_count,
        aspect_ratio,
        prompt,
        idempotency_key,
    ):
        assert requested_draft_id == draft_id
        assert requested_project_id == project_id
        assert user_id == user.id
        assert style == "Editorial"
        assert image_count == 1
        assert aspect_ratio == "4:5"
        assert prompt == "A bright editorial composition"
        assert idempotency_key == request_key
        return [image]

    monkeypatch.setattr(main, "save_generated_images", fake_save)
    response = test_client.post(
        f"/api/v1/projects/{project_id}/images/generate",
        json={
            "draft_id": str(draft_id),
            "style": "Editorial",
            "image_count": 1,
            "aspect_ratio": "4:5",
            "prompt": "A bright editorial composition",
            "idempotency_key": str(request_key),
        },
    )

    assert response.status_code == 201
    assert response.json()[0]["url"] == "/generated-images/example.jpg"


def test_generate_images_requires_supported_aspect_ratio(client):
    test_client, _ = client
    response = test_client.post(
        f"/api/v1/projects/{uuid4()}/images/generate",
        json={
            "draft_id": str(uuid4()),
            "style": "Editorial",
            "image_count": 1,
            "aspect_ratio": "3:7",
            "idempotency_key": str(uuid4()),
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_cloudflare_flux_request_omits_unsupported_seed(monkeypatch):
    captured_payload = None

    class FakeResponse:
        is_success = True
        status_code = 200
        text = ""
        headers = {"cf-ray": "test-ray"}

        @staticmethod
        def json():
            return {"result": {"image": base64.b64encode(b"jpeg-data").decode("ascii")}}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, endpoint, headers, json):
            nonlocal captured_payload
            captured_payload = json
            return FakeResponse()

    monkeypatch.setattr(cloudflare_provider.httpx, "AsyncClient", FakeClient)
    provider = CloudflareImageProvider.__new__(CloudflareImageProvider)
    provider.account_id = "account"
    provider.api_token = "token"

    result = await provider.generate(prompt="A cinematic creator workspace")

    assert captured_payload == {
        "prompt": "A cinematic creator workspace",
        "steps": 4,
    }
    assert result.content == b"jpeg-data"
