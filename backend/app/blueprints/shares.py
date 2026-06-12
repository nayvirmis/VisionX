from flask import Blueprint, g, jsonify, request

from ..errors import ApiError
from ..extensions import db, limiter
from ..models import FeedShare, User
from ..security import USERNAME_RE, require_auth

bp = Blueprint("shares", __name__, url_prefix="/api/shares")


@bp.post("")
@require_auth
@limiter.limit("60 per hour")
def create_share():
    username = str((request.get_json(silent=True) or {}).get("username", "")).strip()
    if not USERNAME_RE.fullmatch(username):
        raise ApiError("Enter a valid VisionX username.", code="invalid_username")
    target = db.session.scalar(
        db.select(User).where(User.username == username, User.is_active.is_(True))
    )
    if not target:
        raise ApiError("VisionX user was not found.", 404, "user_not_found")
    if target.id == g.current_user.id:
        raise ApiError("You cannot share a feed with yourself.", code="self_share")
    existing = db.session.get(FeedShare, (g.current_user.id, target.id))
    if existing:
        raise ApiError("Feed access is already shared.", 409, "share_exists")
    db.session.add(FeedShare(owner_id=g.current_user.id, shared_with_id=target.id))
    db.session.commit()
    return jsonify({"username": target.username}), 201


@bp.get("/outgoing")
@require_auth
def outgoing():
    shares = db.session.scalars(
        db.select(FeedShare)
        .where(FeedShare.owner_id == g.current_user.id)
        .order_by(FeedShare.created_at.desc())
    ).all()
    return jsonify(
        [
            {
                "username": share.shared_with.username,
                "created_at": share.created_at.isoformat(),
            }
            for share in shares
        ]
    )


@bp.get("/incoming")
@require_auth
def incoming():
    shares = db.session.scalars(
        db.select(FeedShare)
        .where(FeedShare.shared_with_id == g.current_user.id)
        .order_by(FeedShare.created_at.desc())
    ).all()
    return jsonify(
        [
            {
                "username": share.owner.username,
                "x_connected": bool(share.owner.x_account),
                "x_username": share.owner.x_account.username if share.owner.x_account else None,
                "created_at": share.created_at.isoformat(),
            }
            for share in shares
        ]
    )


@bp.delete("/<username>")
@require_auth
def delete_share(username):
    target = db.session.scalar(db.select(User).where(User.username == username))
    if not target:
        raise ApiError("VisionX user was not found.", 404, "user_not_found")
    share = db.session.get(FeedShare, (g.current_user.id, target.id))
    if not share:
        raise ApiError("Feed access was not shared.", 404, "share_not_found")
    db.session.delete(share)
    db.session.commit()
    return "", 204
