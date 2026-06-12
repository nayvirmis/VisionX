"""Create the hardened VisionX schema and migrate the legacy schema.

Revision ID: 20260612_01
Revises:
Create Date: 2026-06-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "20260612_01"
down_revision = None
branch_labels = None
depends_on = None


def _tables():
    return set(inspect(op.get_bind()).get_table_names())


def upgrade():
    tables = _tables()

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("username", sa.String(50), nullable=False, unique=True),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.Column("email", sa.String(255), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("last_login", sa.DateTime(timezone=True)),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.create_index("ix_users_username", "users", ["username"], unique=True)
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    tables = _tables()
    if "feed_shares" not in tables:
        op.create_table(
            "feed_shares",
            sa.Column(
                "owner_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                "shared_with_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_feed_shares_shared_with", "feed_shares", ["shared_with_id"])

    op.create_table(
        "x_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("x_user_id", sa.String(64), nullable=False, unique=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("profile_image_url", sa.Text()),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("connected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("replaced_by_hash", sa.String(64)),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_table(
        "oauth_link_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("code_verifier", sa.String(160), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "feed_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("posts", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_feed_cache_expires_at", "feed_cache", ["expires_at"])

    tables = _tables()
    for legacy_table in ("feed_fetches", "user_cookies", "user_tweets"):
        if legacy_table in tables:
            op.drop_table(legacy_table)


def downgrade():
    op.drop_table("feed_cache")
    op.drop_table("oauth_link_states")
    op.drop_table("refresh_tokens")
    op.drop_table("x_accounts")
