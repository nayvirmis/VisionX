from datetime import UTC, datetime

from .extensions import db


def utcnow():
    return datetime.now(UTC)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_login = db.Column(db.DateTime(timezone=True))
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    x_account = db.relationship(
        "XAccount", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    refresh_tokens = db.relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class FeedShare(db.Model):
    __tablename__ = "feed_shares"

    owner_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    shared_with_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    owner = db.relationship("User", foreign_keys=[owner_id])
    shared_with = db.relationship("User", foreign_keys=[shared_with_id])


class XAccount(db.Model):
    __tablename__ = "x_accounts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    x_user_id = db.Column(db.String(64), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    profile_image_url = db.Column(db.Text)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    connected_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="x_account")


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    replaced_by_hash = db.Column(db.String(64))

    user = db.relationship("User", back_populates="refresh_tokens")


class OAuthLinkState(db.Model):
    __tablename__ = "oauth_link_states"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    state_hash = db.Column(db.String(64), unique=True, nullable=False)
    code_verifier = db.Column(db.String(160), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    user = db.relationship("User")


class FeedCache(db.Model):
    __tablename__ = "feed_cache"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    posts = db.Column(db.JSON, nullable=False)
    fetched_at = db.Column(db.DateTime(timezone=True), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)

    owner = db.relationship("User")
