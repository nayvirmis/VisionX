import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app import models  # noqa: F401
from app.config import normalize_database_url
from app.extensions import db

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = normalize_database_url(
    os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
)
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
target_metadata = db.metadata


def get_url():
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline():
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
