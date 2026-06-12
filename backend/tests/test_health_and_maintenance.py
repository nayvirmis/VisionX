from datetime import timedelta

from app.extensions import db
from app.models import FeedCache, User, utcnow


def test_health_endpoints(client):
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200


def test_cleanup_requires_secret(client, alice):
    rejected = client.post("/api/maintenance/cleanup")
    assert rejected.status_code == 401

    user = db.session.scalar(db.select(User).where(User.username == "alice"))
    db.session.add(
        FeedCache(
            owner_id=user.id,
            posts=[],
            fetched_at=utcnow() - timedelta(hours=1),
            expires_at=utcnow() - timedelta(minutes=1),
        )
    )
    db.session.commit()
    cleaned = client.post("/api/maintenance/cleanup", headers={"X-Cron-Secret": "test-cron-secret"})
    assert cleaned.status_code == 200
    assert cleaned.get_json()["deleted"]["feed_cache"] == 1
