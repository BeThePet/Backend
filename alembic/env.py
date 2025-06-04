from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import MetaData, engine_from_config, pool

from alembic import context
from api.db.models import Base as APIBase
from api.db.session import DATABASE_URL
from chatbot.src.models.chat import Base as ChatbotBase

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Combine metadata from both bases
def combine_metadata(*args):
    combined_metadata = MetaData()
    for metadata in args:
        for table in metadata.tables.values():
            table.tometadata(combined_metadata)
    return combined_metadata


# target_metadata 설정
target_metadata = combine_metadata(APIBase.metadata, ChatbotBase.metadata)


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
