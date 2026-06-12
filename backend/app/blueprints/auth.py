from datetime import UTC, datetime

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..errors import ApiError
from ..extensions import db, limiter
from ..models import RefreshToken, User, utcnow
from ..security import (
    create_access_token,
    hash_password,
    issue_refresh_token,
    require_auth,
    rotate_refresh_token,
    token_hash,
    validate_registration,
    verify_password,
)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def user_payload(user):
    return {
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "x_account": (
            {
                "username": user.x_account.username,
                "display_name": user.x_account.display_name,
                "profile_image_url": user.x_account.profile_image_url,
                "verified": user.x_account.verified,
            }
            if user.x_account
            else None
        ),
    }


def token_payload(user):
    refresh_token, _ = issue_refresh_token(user)
    return {
        "access_token": create_access_token(user),
        "refresh_token": refresh_token,
        "expires_in": int(current_app.config["ACCESS_TOKEN_TTL"].total_seconds()),
        "user": user_payload(user),
    }


@bp.post("/register")
@limiter.limit("10 per hour")
def register():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    validate_registration(username, email, password)
    user = User(username=username, email=email, password_hash=hash_password(password))
    db.session.add(user)
    try:
        db.session.flush()
        payload = token_payload(user)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ApiError("Username or email already exists.", 409, "account_exists") from exc
    return jsonify(payload), 201


@bp.post("/login")
@limiter.limit("20 per hour")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    user = db.session.scalar(db.select(User).where(User.username == username))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise ApiError("Invalid username or password.", 401, "invalid_credentials")
    user.last_login = utcnow()
    payload = token_payload(user)
    db.session.commit()
    return jsonify(payload)


@bp.post("/refresh")
@limiter.limit("60 per hour")
def refresh():
    raw_token = str((request.get_json(silent=True) or {}).get("refresh_token", ""))
    user, replacement = rotate_refresh_token(raw_token)
    db.session.commit()
    return jsonify(
        {
            "access_token": create_access_token(user),
            "refresh_token": replacement,
            "expires_in": int(current_app.config["ACCESS_TOKEN_TTL"].total_seconds()),
        }
    )


@bp.post("/logout")
def logout():
    raw_token = str((request.get_json(silent=True) or {}).get("refresh_token", ""))
    if raw_token:
        record = db.session.scalar(
            db.select(RefreshToken).where(RefreshToken.token_hash == token_hash(raw_token))
        )
        if record and record.revoked_at is None:
            record.revoked_at = datetime.now(UTC)
            db.session.commit()
    return jsonify({"message": "Logged out."})


@bp.get("/me")
@require_auth
def me():
    return jsonify(user_payload(g.current_user))


@bp.delete("/account")
@require_auth
def delete_account():
    password = str((request.get_json(silent=True) or {}).get("password", ""))
    if not password or not verify_password(password, g.current_user.password_hash):
        raise ApiError("Password confirmation is incorrect.", 401, "invalid_password")
    db.session.delete(g.current_user)
    db.session.commit()
    return "", 204
