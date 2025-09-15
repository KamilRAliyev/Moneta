from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Project imports: settings and model bases for each DB
from server.settings import DATABASE_PATHS
from server.models.main import Base as MainBase
from server.models.configurations import Base as ConfigBase

# Alembic Config object, provides access to values within the .ini file in use.
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_selected_db_and_metadata():
    """Pick the target DB from `-x db=...` and return (name, url, metadata)."""
    x_args = context.get_x_argument(as_dictionary=True)
    db_name = x_args.get("db", "main")

    if db_name not in DATABASE_PATHS:
        raise SystemExit(
            f"Unknown db '{db_name}'. Valid keys: {', '.join(DATABASE_PATHS.keys())}"
        )

    db_path = Path(DATABASE_PATHS[db_name]).resolve()
    url = f"sqlite:///{db_path}"

    # Choose the metadata per database
    if db_name == "main":
        metadata = MainBase.metadata
    elif db_name == "configurations":
        metadata = ConfigBase.metadata
    else:
        # Fallback if more DBs are added later without wiring here
        raise SystemExit(
            f"No metadata mapping set for db '{db_name}'. Please update env.py."
        )

    return db_name, url, metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode for the selected DB."""
    _, url, target_metadata = get_selected_db_and_metadata()
    # Ensure the dynamic URL is set so script directory may reflect it if needed
    config.set_main_option("sqlalchemy.url", url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode for the selected DB."""
    _, url, target_metadata = get_selected_db_and_metadata()
    # Override URL from ini based on selected db
    config.set_main_option("sqlalchemy.url", url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
