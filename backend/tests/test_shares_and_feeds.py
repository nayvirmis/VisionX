from datetime import timedelta

from app.errors import UpstreamError
from app.extensions import db
from app.models import FeedCache, User, XAccount, utcnow

from .conftest import auth


def test_share_lists_and_revoke(client, alice, bob):
    created = client.post(
        "/api/shares",
        headers=auth(alice["access_token"]),
        json={"username": "bob"},
    )
    assert created.status_code == 201

    outgoing = client.get("/api/shares/outgoing", headers=auth(alice["access_token"])).get_json()
    incoming = client.get("/api/shares/incoming", headers=auth(bob["access_token"])).get_json()
    assert outgoing[0]["username"] == "bob"
    assert incoming[0]["username"] == "alice"
    assert incoming[0]["x_connected"] is False

    removed = client.delete("/api/shares/bob", headers=auth(alice["access_token"]))
    assert removed.status_code == 204
    assert client.get("/api/shares/incoming", headers=auth(bob["access_token"])).get_json() == []


def test_feed_requires_share_and_connected_owner(client, alice, bob):
    forbidden = client.get("/api/feeds/alice", headers=auth(bob["access_token"]))
    assert forbidden.status_code == 403

    client.post(
        "/api/shares",
        headers=auth(alice["access_token"]),
        json={"username": "bob"},
    )
    not_connected = client.get("/api/feeds/alice", headers=auth(bob["access_token"]))
    assert not_connected.status_code == 409
    assert not_connected.get_json()["error"]["code"] == "x_account_not_connected"


def test_feed_fetch_and_cache(client, app, alice, bob, monkeypatch):
    client.post(
        "/api/shares",
        headers=auth(alice["access_token"]),
        json={"username": "bob"},
    )
    owner = db.session.scalar(db.select(User).where(User.username == "alice"))
    db.session.add(
        XAccount(
            user_id=owner.id,
            x_user_id="123",
            username="alice_x",
            display_name="Alice X",
        )
    )
    db.session.commit()

    calls = []

    def fake_posts(x_user_id, account):
        calls.append(x_user_id)
        return [{"id": "1", "text": "Public post", "author": {"username": account.username}}]

    monkeypatch.setattr("app.blueprints.feeds.get_public_posts", fake_posts)

    first = client.get("/api/feeds/alice", headers=auth(bob["access_token"]))
    second = client.get("/api/feeds/alice", headers=auth(bob["access_token"]))
    assert first.status_code == 200
    assert first.get_json()["cached"] is False
    assert second.get_json()["cached"] is True
    assert second.get_json()["count"] == 1
    assert calls == ["123"]


def test_expired_cache_refreshes(client, alice, bob, monkeypatch):
    client.post(
        "/api/shares",
        headers=auth(alice["access_token"]),
        json={"username": "bob"},
    )
    owner = db.session.scalar(db.select(User).where(User.username == "alice"))
    db.session.add(
        XAccount(
            user_id=owner.id,
            x_user_id="123",
            username="alice_x",
            display_name="Alice X",
        )
    )
    db.session.add(
        FeedCache(
            owner_id=owner.id,
            posts=[{"id": "old"}],
            fetched_at=utcnow() - timedelta(hours=1),
            expires_at=utcnow() - timedelta(minutes=1),
        )
    )
    db.session.commit()
    monkeypatch.setattr(
        "app.blueprints.feeds.get_public_posts",
        lambda *_: [{"id": "new", "text": "Updated"}],
    )
    response = client.get("/api/feeds/alice", headers=auth(bob["access_token"]))
    assert response.get_json()["posts"][0]["id"] == "new"


def test_upstream_error_is_structured(client, alice, bob, monkeypatch):
    client.post(
        "/api/shares",
        headers=auth(alice["access_token"]),
        json={"username": "bob"},
    )
    owner = db.session.scalar(db.select(User).where(User.username == "alice"))
    db.session.add(
        XAccount(
            user_id=owner.id,
            x_user_id="123",
            username="alice_x",
            display_name="Alice X",
        )
    )
    db.session.commit()

    def fail(*_):
        raise UpstreamError("X API rate limit reached.", 503, "x_rate_limited")

    monkeypatch.setattr("app.blueprints.feeds.get_public_posts", fail)
    response = client.get("/api/feeds/alice", headers=auth(bob["access_token"]))
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "x_rate_limited"
