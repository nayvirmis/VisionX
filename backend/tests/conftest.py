import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username="alice", email="alice@example.com", password="Password1"):
    return client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )


@pytest.fixture()
def alice(client):
    response = register(client)
    payload = response.get_json()
    return {
        "username": "alice",
        "password": "Password1",
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
    }


@pytest.fixture()
def bob(client):
    response = register(client, "bob", "bob@example.com", "Password2")
    payload = response.get_json()
    return {
        "username": "bob",
        "password": "Password2",
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
    }


def auth(token):
    return {"Authorization": f"Bearer {token}"}
