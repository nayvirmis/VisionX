import base64
import hashlib
import secrets
from datetime import UTC

from flask import Blueprint, current_app, g, jsonify, request

from ..errors import ApiError
from ..extensions import db, limiter
from ..models import FeedCache, OAuthLinkState, XAccount, utcnow
from ..security import require_auth, token_hash
from ..services import x_api

bp = Blueprint("x_accounts", __name__, url_prefix="/api/x")


@bp.post("/oauth/start")
@require_auth
@limiter.limit("20 per hour")
def oauth_start():
    if not current_app.config["X_CLIENT_ID"] or not current_app.config["X_CLIENT_SECRET"]:
        raise ApiError("X OAuth is not configured.", 503, "x_not_configured")
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    db.session.add(
        OAuthLinkState(
            user_id=g.current_user.id,
            state_hash=token_hash(state),
            code_verifier=verifier,
            expires_at=utcnow() + current_app.config["OAUTH_STATE_TTL"],
        )
    )
    db.session.commit()
    return jsonify({"authorize_url": x_api.authorization_url(state, challenge)})


@bp.get("/oauth/callback")
@limiter.limit("60 per hour")
def oauth_callback():
    state = request.args.get("state", "")
    code = request.args.get("code", "")
    if not state or not code:
        raise ApiError("X OAuth callback is incomplete.", code="invalid_oauth_callback")
    record = db.session.scalar(
        db.select(OAuthLinkState)
        .where(OAuthLinkState.state_hash == token_hash(state))
        .with_for_update()
    )
    if (
        not record
        or record.used_at is not None
        or record.expires_at.replace(tzinfo=UTC) <= utcnow()
    ):
        raise ApiError("OAuth state is invalid or expired.", 400, "invalid_oauth_state")
    record.used_at = utcnow()
    db.session.commit()

    access_token = x_api.exchange_code(code, record.code_verifier)
    profile = x_api.get_authenticated_user(access_token)
    if profile.get("protected"):
        raise ApiError(
            "Protected X accounts are not supported by VisionX.",
            400,
            "protected_x_account",
        )
    duplicate = db.session.scalar(
        db.select(XAccount).where(
            XAccount.x_user_id == profile["id"], XAccount.user_id != record.user_id
        )
    )
    if duplicate:
        raise ApiError(
            "This X account is already connected to another VisionX account.",
            409,
            "x_account_in_use",
        )
    account = db.session.scalar(db.select(XAccount).where(XAccount.user_id == record.user_id))
    if not account:
        account = XAccount(user_id=record.user_id, x_user_id=profile["id"])
        db.session.add(account)
    account.x_user_id = profile["id"]
    account.username = profile["username"]
    account.display_name = profile["name"]
    account.profile_image_url = profile.get("profile_image_url")
    account.verified = bool(profile.get("verified"))
    account.connected_at = utcnow()
    db.session.commit()
    return (
        "<!doctype html><title>VisionX connected</title>"
        "<style>body{font:16px system-ui;max-width:560px;margin:80px auto;padding:24px}"
        "h1{color:#146ef5}</style><h1>X account connected</h1>"
        "<p>You can close this tab and return to the VisionX extension.</p>"
    )


@bp.get("/account")
@require_auth
def get_account():
    account = g.current_user.x_account
    return jsonify(
        {
            "connected": bool(account),
            "account": (
                {
                    "username": account.username,
                    "display_name": account.display_name,
                    "profile_image_url": account.profile_image_url,
                    "verified": account.verified,
                }
                if account
                else None
            ),
        }
    )


@bp.delete("/account")
@require_auth
def disconnect_account():
    account = g.current_user.x_account
    if account:
        cache = db.session.scalar(
            db.select(FeedCache).where(FeedCache.owner_id == g.current_user.id)
        )
        if cache:
            db.session.delete(cache)
        db.session.delete(account)
        db.session.commit()
    return "", 204
