from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

import server.main as main
from backend.database.db_store import get_db
from core.config import get_settings
from core.security import create_access_token, decode_access_token


async def unused_db():
    yield object()


@pytest.fixture
def client():
    main.app.dependency_overrides[get_db] = unused_db
    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


def test_register_returns_public_user(client, monkeypatch):
    user_id = uuid4()

    async def fake_register(request, db):
        assert request.full_name == "Alex Morgan"
        return SimpleNamespace(id=user_id, full_name=request.full_name, email=request.email)

    monkeypatch.setattr(main, "register_user", fake_register)
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Alex Morgan", "email": "alex@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    assert response.json() == {
        "id": str(user_id),
        "full_name": "Alex Morgan",
        "email": "alex@example.com",
    }


def test_duplicate_registration_returns_conflict(client, monkeypatch):
    async def fake_register(request, db):
        return False

    monkeypatch.setattr(main, "register_user", fake_register)
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Alex Morgan", "email": "alex@example.com", "password": "password123"},
    )
    assert response.status_code == 409


def test_login_returns_decodable_bearer_token(client, monkeypatch):
    user_id = uuid4()

    async def fake_login(request, db):
        return SimpleNamespace(id=user_id)

    monkeypatch.setattr(main, "login_user", fake_login)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert decode_access_token(response.json()["access_token"])["sub"] == str(user_id)


def test_invalid_login_is_unauthorized(client, monkeypatch):
    async def fake_login(request, db):
        return False

    monkeypatch.setattr(main, "login_user", fake_login)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_users_me_requires_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_expired_token_is_rejected():
    token = create_access_token(str(uuid4()), now=datetime.now(UTC) - timedelta(days=1))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_users_me_accepts_valid_bearer_token(client):
    user_id = uuid4()
    user = SimpleNamespace(id=user_id, full_name="Alex Morgan", email="alex@example.com")

    async def fake_current_user():
        return user

    main.app.dependency_overrides[main.get_current_user] = fake_current_user
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {create_access_token(str(user_id))}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(user_id)


def test_access_token_has_required_claims():
    settings = get_settings()
    claims = decode_access_token(create_access_token(str(uuid4())))
    assert {"sub", "iat", "exp", "jti", "iss", "aud"} <= claims.keys()
    assert claims["iss"] == settings.jwt_issuer
    assert claims["aud"] == settings.jwt_audience
