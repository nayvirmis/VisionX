import hashlib
import re
import secrets
from datetime import UTC, datetime
from functools import wraps

import bcrypt
import jwt
from flask import current_app, g, request

from .errors import ApiError
from .extensions import db
from .models import RefreshToken, User

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,50}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def utcnow():
    return datetime.now(UTC)


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def validate_registration(username, email, password):
    if not USERNAME_RE.fullmatch(username):
        raise ApiError(
            "Username must be 3-50 characters and use only letters, numbers, or underscores.",
            code="invalid_username",
        )
    if not EMAIL_RE.fullmatch(email) or len(email) > 255:
        raise ApiError("Enter a valid email address.", code="invalid_email")
    if (
        len(password) < 8
        or len(password.encode()) > 72
        or not re.search(r"[A-Z]", password)
        or not re.search(r"[a-z]", password)
        or not re.search(r"\d", password)
    ):
        raise ApiError(
            "Password must be at least 8 characters and include "
            "uppercase, lowercase, and a number, with a maximum of 72 bytes.",
            code="weak_password",
        )


def create_access_token(user):
    now = utcnow()
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "iat": now,
        "exp": now + current_app.config["ACCESS_TOKEN_TTL"],
        "type": "access",
        "jti": secrets.token_hex(12),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def issue_refresh_token(user):
    raw_token = secrets.token_urlsafe(48)
    record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash(raw_token),
        expires_at=utcnow() + current_app.config["REFRESH_TOKEN_TTL"],
    )
    db.session.add(record)
    return raw_token, record


def rotate_refresh_token(raw_token):
    digest = token_hash(raw_token)
    record = db.session.scalar(
        db.select(RefreshToken).where(RefreshToken.token_hash == digest).with_for_update()
    )
    if record and record.revoked_at is not None and record.replaced_by_hash:
        now = utcnow()
        db.session.query(RefreshToken).filter(
            RefreshToken.user_id == record.user_id,
            RefreshToken.revoked_at.is_(None),
        ).update({RefreshToken.revoked_at: now})
        db.session.commit()
        raise ApiError(
            "Refresh token reuse was detected. Sign in again.",
            401,
            "refresh_token_reused",
        )
    if not record or record.revoked_at is not None:
        raise ApiError("Refresh token is invalid or expired.", 401, "invalid_refresh_token")
    if record.expires_at.replace(tzinfo=UTC) <= utcnow():
        record.revoked_at = utcnow()
        db.session.commit()
        raise ApiError("Refresh token is invalid or expired.", 401, "invalid_refresh_token")

    replacement, new_record = issue_refresh_token(record.user)
    record.revoked_at = utcnow()
    record.replaced_by_hash = new_record.token_hash
    return record.user, replacement


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise ApiError("Authentication is required.", 401, "authentication_required")
        token = header.removeprefix("Bearer ").strip()
        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise ApiError("Access token has expired.", 401, "token_expired") from exc
        except jwt.InvalidTokenError as exc:
            raise ApiError("Access token is invalid.", 401, "invalid_token") from exc
        if payload.get("type") != "access":
            raise ApiError("Access token is invalid.", 401, "invalid_token")
        try:
            user_id = int(payload["sub"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ApiError("Access token is invalid.", 401, "invalid_token") from exc
        user = db.session.get(User, user_id)
        if not user or not user.is_active:
            raise ApiError("Account is unavailable.", 401, "account_unavailable")
        g.current_user = user
        return view(*args, **kwargs)

    return wrapped
