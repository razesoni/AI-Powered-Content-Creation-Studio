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
def user():
    return SimpleNamespace(id=uuid4(), full_name="Alex Morgan", email="alex@example.com")


@pytest.fixture
def client(user):
    async def current_user():
        return user

    main.app.dependency_overrides[get_db] = unused_db
    main.app.dependency_overrides[main.get_current_user] = current_user
    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


def project(user_id):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        title="Design Notes",
        description="Weekly design lessons",
        platform="LinkedIn",
        content_type="Article",
        target_audience="Product designers",
        tone="Thoughtful and clear",
        created_at=now,
        updated_at=now,
    )


def test_create_project_for_current_user(client, user, monkeypatch):
    created = project(user.id)

    async def fake_create(request, user_id, db):
        assert user_id == user.id
        assert request.title == "Design Notes"
        return created

    monkeypatch.setattr(main, "create_project", fake_create)
    response = client.post(
        "/api/v1/projects",
        json={
            "title": "Design Notes",
            "description": "Weekly design lessons",
            "platform": "LinkedIn",
            "content_type": "Article",
            "target_audience": "Product designers",
            "tone": "Thoughtful and clear",
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == str(created.id)


def test_list_projects_for_current_user(client, user, monkeypatch):
    item = project(user.id)

    async def fake_list(user_id, db):
        assert user_id == user.id
        return [item]

    monkeypatch.setattr(main, "get_user_projects", fake_list)
    response = client.get("/api/v1/projects?limit=100")
    assert response.status_code == 200
    assert [value["id"] for value in response.json()] == [str(item.id)]


def test_delete_project_for_current_user(client, user, monkeypatch):
    project_id = uuid4()

    async def fake_delete(requested_id, user_id, db):
        return requested_id == project_id and user_id == user.id

    monkeypatch.setattr(main, "delete_user_project", fake_delete)
    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204


def test_delete_missing_or_foreign_project_returns_not_found(client, monkeypatch):
    async def fake_delete(project_id, user_id, db):
        return False

    monkeypatch.setattr(main, "delete_user_project", fake_delete)
    response = client.delete(f"/api/v1/projects/{uuid4()}")
    assert response.status_code == 404


def test_project_rejects_unsupported_platform(client):
    response = client.post(
        "/api/v1/projects",
        json={
            "title": "Design Notes",
            "description": "Weekly design lessons",
            "platform": "MySpace",
            "content_type": "Article",
            "target_audience": "Product designers",
            "tone": "Thoughtful and clear",
        },
    )
    assert response.status_code == 422
