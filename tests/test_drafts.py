from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import server.main as main
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


def test_generate_draft_uses_the_frontend_request_shape(client, monkeypatch):
    test_client, user = client
    project_id, outline_id = uuid4(), uuid4()
    now = datetime.now(UTC)
    draft = SimpleNamespace(
        id=uuid4(),
        project_id=project_id,
        outline_id=outline_id,
        title="Content planning routine",
        content="# Content planning routine\n\nStart with one theme.",
        format="markdown",
        version=1,
        created_at=now,
        updated_at=now,
    )

    async def fake_save(
        requested_outline_id,
        requested_project_id,
        user_id,
        db,
        draft_format,
        instructions,
        idempotency_key,
    ):
        assert requested_outline_id == outline_id
        assert requested_project_id == project_id
        assert user_id == user.id
        assert draft_format == "markdown"
        assert instructions == "Keep it concise"
        assert idempotency_key is not None
        return draft

    monkeypatch.setattr(main, "save_generated_drafts", fake_save)
    response = test_client.post(
        f"/api/v1/projects/{project_id}/drafts/generate",
        json={
            "outline_id": str(outline_id),
            "format": "markdown",
            "instructions": "Keep it concise",
            "idempotency_key": str(uuid4()),
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == str(draft.id)
    assert response.json()["content"] == draft.content
