from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_legacy_migration_preserves_users_and_shares(tmp_path, monkeypatch):
    database_path = tmp_path / "legacy.db"
    database_url = f"sqlite+pysqlite:///{database_path}"
    engine = create_engine(database_url)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE feed_shares (
                    owner_id INTEGER NOT NULL,
                    shared_with_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (owner_id, shared_with_id)
                )
                """
            )
        )
        for table in ("feed_fetches", "user_cookies", "user_tweets"):
            connection.execute(text(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)"))
        connection.execute(
            text(
                """
                INSERT INTO users (id, username, password_hash, email)
                VALUES
                    (1, 'alice', '$2b$legacy-alice', 'alice@example.com'),
                    (2, 'bob', '$2b$legacy-bob', 'bob@example.com')
                """
            )
        )
        connection.execute(text("INSERT INTO feed_shares (owner_id, shared_with_id) VALUES (1, 2)"))

    monkeypatch.setenv("DATABASE_URL", database_url)
    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")

    with engine.connect() as connection:
        users = connection.execute(
            text("SELECT username, password_hash FROM users ORDER BY id")
        ).all()
        shares = connection.execute(text("SELECT owner_id, shared_with_id FROM feed_shares")).all()

    tables = set(inspect(engine).get_table_names())
    assert users == [
        ("alice", "$2b$legacy-alice"),
        ("bob", "$2b$legacy-bob"),
    ]
    assert shares == [(1, 2)]
    assert {"x_accounts", "refresh_tokens", "oauth_link_states", "feed_cache"} <= tables
    assert {"feed_fetches", "user_cookies", "user_tweets"}.isdisjoint(tables)
