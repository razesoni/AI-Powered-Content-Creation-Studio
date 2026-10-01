from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import server.main as main
from backend.ai.llm.content_generation import IdeaGenerationError
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


def idea(project_id):
    return SimpleNamespace(
        id=uuid4(),
        project_id=project_id,
        title="A practical content habit",
        concept_summary="A useful idea for creators who want a sustainable process.",
        hook="Consistency starts with a smaller promise.",
        platform="Instagram",
        is_selected=False,
        created_at=datetime.now(UTC),
    )


def test_generate_ideas_returns_saved_ideas(client, monkeypatch):
    test_client, user = client
    project_id = uuid4()
    saved = [idea(project_id), idea(project_id)]

    async def fake_save(request, requested_project_id, user_id, db, idempotency_key):
        assert request.topic == "creative habits"
        assert request.count == 2
        assert request.tone == "Warm and practical"
        assert request.instructions == "Keep them practical"
        assert requested_project_id == project_id
        assert user_id == user.id
        assert idempotency_key == request.idempotency_key
        return saved

    monkeypatch.setattr(main, "save_generated_ideas", fake_save)
    response = test_client.post(
        f"/api/v1/projects/{project_id}/ideas/generate",
        json={
            "topic": "creative habits",
            "count": 2,
            "tone": "Warm and practical",
            "instructions": "Keep them practical",
            "idempotency_key": str(uuid4()),
        },
    )
    assert response.status_code == 201
    assert [item["id"] for item in response.json()] == [str(item.id) for item in saved]


def test_list_ideas_returns_the_current_users_project_ideas(client, monkeypatch):
    test_client, user = client
    project_id = uuid4()
    saved = [idea(project_id)]

    async def fake_list(requested_project_id, user_id, db):
        assert requested_project_id == project_id
        assert user_id == user.id
        return saved

    monkeypatch.setattr(main, "get_project_ideas", fake_list)
    response = test_client.get(f"/api/v1/projects/{project_id}/ideas")
    assert response.status_code == 200
    assert response.json()[0]["project_id"] == str(project_id)


def test_generate_outline_passes_the_request_idempotency_key(client, monkeypatch):
    test_client, user = client
    project_id, idea_id, idempotency_key = uuid4(), uuid4(), uuid4()
    now = datetime.now(UTC)
    outline = SimpleNamespace(
        id=uuid4(),
        project_id=project_id,
        idea_id=idea_id,
        title="A practical outline",
        outline_data={"sections": []},
        version=1,
        created_at=now,
        updated_at=now,
    )

    async def fake_save(requested_idea_id, requested_project_id, user_id, db, request_key):
        assert requested_idea_id == idea_id
        assert requested_project_id == project_id
        assert user_id == user.id
        assert request_key == idempotency_key
        return outline

    monkeypatch.setattr(main, "save_generated_outlines", fake_save)
    response = test_client.post(
        f"/api/v1/projects/{project_id}/outlines/generate",
        json={"idea_id": str(idea_id), "idempotency_key": str(idempotency_key)},
    )
    assert response.status_code == 201
    assert response.json()["id"] == str(outline.id)


def test_provider_failure_returns_a_clear_gateway_error(client, monkeypatch):
    test_client, _ = client

    async def fake_save(*args):
        raise IdeaGenerationError(
            "Gemini could not generate ideas. Check GEMINI_API_KEY and GEMINI_MODEL."
        )

    monkeypatch.setattr(main, "save_generated_ideas", fake_save)
    response = test_client.post(
        f"/api/v1/projects/{uuid4()}/ideas/generate",
        json={"topic": "creative habits", "count": 3, "idempotency_key": str(uuid4())},
    )
    assert response.status_code == 502
    assert (
        response.json()["detail"]
        == "Gemini could not generate ideas. Check GEMINI_API_KEY and GEMINI_MODEL."
    )
