from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from app.extensions import db
from app.models import OAuthLinkState, XAccount, utcnow

from .conftest import auth


def start_oauth(client, access_token):
    response = client.post("/api/x/oauth/start", headers=auth(access_token))
    assert response.status_code == 200
    url = response.get_json()["authorize_url"]
    return parse_qs(urlparse(url).query)["state"][0]


def test_oauth_links_public_account_and_state_is_single_use(client, alice, monkeypatch):
    state = start_oauth(client, alice["access_token"])
    monkeypatch.setattr("app.blueprints.x_accounts.x_api.exchange_code", lambda *_: "token")
    monkeypatch.setattr(
        "app.blueprints.x_accounts.x_api.get_authenticated_user",
        lambda *_: {
            "id": "x-1",
            "username": "alice_x",
            "name": "Alice X",
            "protected": False,
            "verified": True,
            "profile_image_url": "https://example.com/avatar.png",
        },
    )
    linked = client.get("/api/x/oauth/callback", query_string={"state": state, "code": "code"})
    assert linked.status_code == 200
    assert db.session.scalar(db.select(XAccount)).username == "alice_x"

    reused = client.get("/api/x/oauth/callback", query_string={"state": state, "code": "code"})
    assert reused.status_code == 400


def test_oauth_rejects_protected_account(client, alice, monkeypatch):
    state = start_oauth(client, alice["access_token"])
    monkeypatch.setattr("app.blueprints.x_accounts.x_api.exchange_code", lambda *_: "token")
    monkeypatch.setattr(
        "app.blueprints.x_accounts.x_api.get_authenticated_user",
        lambda *_: {
            "id": "x-2",
            "username": "private_x",
            "name": "Private",
            "protected": True,
        },
    )
    response = client.get("/api/x/oauth/callback", query_string={"state": state, "code": "code"})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "protected_x_account"
    reused = client.get("/api/x/oauth/callback", query_string={"state": state, "code": "code"})
    assert reused.status_code == 400
    assert reused.get_json()["error"]["code"] == "invalid_oauth_state"


def test_expired_oauth_state_is_rejected(client, alice):
    state = start_oauth(client, alice["access_token"])
    record = db.session.scalar(db.select(OAuthLinkState))
    record.expires_at = utcnow() - timedelta(seconds=1)
    db.session.commit()
    response = client.get("/api/x/oauth/callback", query_string={"state": state, "code": "code"})
    assert response.status_code == 400


def test_disconnect_x_account(client, alice):
    account_response = client.get("/api/x/account", headers=auth(alice["access_token"]))
    assert account_response.get_json()["connected"] is False
    disconnected = client.delete("/api/x/account", headers=auth(alice["access_token"]))
    assert disconnected.status_code == 204
