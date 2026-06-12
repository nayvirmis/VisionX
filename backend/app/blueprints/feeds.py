from datetime import UTC

from flask import Blueprint, current_app, g, jsonify

from ..errors import ApiError
from ..extensions import db, limiter
from ..models import FeedCache, FeedShare, User, utcnow
from ..security import require_auth
from ..services.x_api import get_public_posts

bp = Blueprint("feeds", __name__, url_prefix="/api/feeds")


@bp.get("/<username>")
@require_auth
@limiter.limit("120 per hour")
def get_feed(username):
    owner = db.session.scalar(
        db.select(User).where(User.username == username, User.is_active.is_(True))
    )
    if not owner:
        raise ApiError("VisionX user was not found.", 404, "user_not_found")
    if not db.session.get(FeedShare, (owner.id, g.current_user.id)):
        raise ApiError("This feed has not been shared with you.", 403, "feed_forbidden")
    if not owner.x_account:
        raise ApiError(
            "The owner has not connected a public X account.",
            409,
            "x_account_not_connected",
        )

    now = utcnow()
    cache = db.session.scalar(db.select(FeedCache).where(FeedCache.owner_id == owner.id))
    if cache and cache.expires_at.replace(tzinfo=UTC) > now:
        posts = cache.posts
        fetched_at = cache.fetched_at
        cached = True
    else:
        posts = get_public_posts(owner.x_account.x_user_id, owner.x_account)
        fetched_at = now
        expires_at = now + current_app.config["FEED_CACHE_TTL"]
        if cache:
            cache.posts = posts
            cache.fetched_at = fetched_at
            cache.expires_at = expires_at
        else:
            db.session.add(
                FeedCache(
                    owner_id=owner.id,
                    posts=posts,
                    fetched_at=fetched_at,
                    expires_at=expires_at,
                )
            )
        db.session.commit()
        cached = False

    return jsonify(
        {
            "posts": posts,
            "source_user": owner.username,
            "x_username": owner.x_account.username,
            "fetched_at": fetched_at.isoformat(),
            "cached": cached,
            "count": len(posts),
        }
    )
