import secrets

from flask import Blueprint, current_app, jsonify, request

from ..errors import ApiError
from ..extensions import db
from ..models import FeedCache, OAuthLinkState, RefreshToken, utcnow

bp = Blueprint("maintenance", __name__, url_prefix="/api/maintenance")


@bp.post("/cleanup")
def cleanup():
    provided = request.headers.get("X-Cron-Secret", "")
    expected = current_app.config["CRON_SECRET"]
    if not provided or not secrets.compare_digest(provided, expected):
        raise ApiError("Maintenance authentication failed.", 401, "invalid_cron_secret")
    now = utcnow()
    deleted = {
        "feed_cache": db.session.query(FeedCache).filter(FeedCache.expires_at < now).delete(),
        "oauth_states": db.session.query(OAuthLinkState)
        .filter(OAuthLinkState.expires_at < now)
        .delete(),
        "refresh_tokens": db.session.query(RefreshToken)
        .filter(RefreshToken.expires_at < now)
        .delete(),
    }
    db.session.commit()
    return jsonify({"deleted": deleted})
