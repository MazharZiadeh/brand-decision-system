"""Async DB fixtures for integration tests.

The `_apply_migrations` session-scoped fixture brings the schema to head once
at the start of the test run; `db_session` then wraps each test in a
transaction that rolls back at the end so tests do not pollute each other.
"""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import get_settings


def _alembic_config() -> Config:
    cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    return cfg


@pytest.fixture(scope="session")
def _apply_migrations() -> None:
    """Bring the database schema to head once per test session.

    Tests assume the schema exists. Migration verification has its own
    dedicated test in `test_migration.py` that exercises down + up cycles.
    """
    cfg = _alembic_config()
    command.upgrade(cfg, "head")


@pytest_asyncio.fixture(scope="session")
async def engine(_apply_migrations) -> AsyncIterator:
    settings = get_settings()
    url = settings.database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    eng = create_async_engine(url, echo=False, pool_pre_ping=True)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncIterator[AsyncSession]:
    """Function-scoped session that rolls back at end-of-test."""
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
