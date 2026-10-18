import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Import the Alembic context helper object
from alembic import context

# 1. FIXED: Inject your root project path so Python can find your app directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. FIXED: Import your base model registry metadata container
# (If your Base or models are located in a different path, adjust this import)
from app.models import Base 

# This is the Alembic Config object, which provides access to values within the .ini file.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. FIXED: Assign your model metadata so --autogenerate knows what tables look like
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an AsyncEngine connection pipeline."""
    # Read the connection URL string from your configuration settings
    url = config.get_main_option("sqlalchemy.url")
    
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    def do_run_migrations(connection):
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

    async def run_async_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
