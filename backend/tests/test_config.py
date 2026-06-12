from app.config import normalize_database_url


def test_render_postgres_urls_use_the_psycopg_driver():
    assert (
        normalize_database_url("postgresql://user:pass@host/database")
        == "postgresql+psycopg://user:pass@host/database"
    )
    assert (
        normalize_database_url("postgres://user:pass@host/database")
        == "postgresql+psycopg://user:pass@host/database"
    )
