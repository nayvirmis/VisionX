from app.extensions import db
from app.models import RefreshToken, User

from .conftest import auth, register


def test_registration_login_profile_and_delete(client):
    response = register(client)
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["user"]["username"] == "alice"
    assert payload["access_token"]
    assert payload["refresh_token"]

    profile = client.get("/api/auth/me", headers=auth(payload["access_token"]))
    assert profile.status_code == 200
    assert profile.get_json()["email"] == "alice@example.com"

    login = client.post("/api/auth/login", json={"username": "alice", "password": "Password1"})
    assert login.status_code == 200
    assert login.get_json()["user"]["last_login"] is not None

    deleted = client.delete(
        "/api/auth/account",
        headers=auth(payload["access_token"]),
        json={"password": "Password1"},
    )
    assert deleted.status_code == 204
    assert db.session.scalar(db.select(User).where(User.username == "alice")) is None


def test_registration_validation_and_duplicate(client):
    weak = register(client, password="short")
    assert weak.status_code == 400
    assert weak.get_json()["error"]["code"] == "weak_password"

    assert register(client).status_code == 201
    duplicate = register(client)
    assert duplicate.status_code == 409

    oversized = register(
        client,
        "charlie",
        "charlie@example.com",
        f"Aa1{'x' * 70}",
    )
    assert oversized.status_code == 400


def test_refresh_tokens_rotate_and_cannot_be_reused(client, alice):
    first = client.post("/api/auth/refresh", json={"refresh_token": alice["refresh_token"]})
    assert first.status_code == 200
    replacement = first.get_json()["refresh_token"]
    assert replacement != alice["refresh_token"]

    reused = client.post("/api/auth/refresh", json={"refresh_token": alice["refresh_token"]})
    assert reused.status_code == 401
    assert reused.get_json()["error"]["code"] == "refresh_token_reused"

    logout = client.post("/api/auth/logout", json={"refresh_token": replacement})
    assert logout.status_code == 200
    assert db.session.scalar(db.select(RefreshToken).where(RefreshToken.revoked_at.is_not(None)))

    revoked_replacement = client.post("/api/auth/refresh", json={"refresh_token": replacement})
    assert revoked_replacement.status_code == 401


def test_protected_route_requires_access_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"
