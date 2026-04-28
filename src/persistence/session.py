from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import get_settings


def _make_engine():
    """Build the async engine from Settings.

    Accepts both `postgresql://` and `postgresql+asyncpg://` URLs; the former
    is rewritten so SQLAlchemy uses the asyncpg driver. Other async drivers
    (e.g. psycopg-async) are left alone.
    """
    settings = get_settings()
    url = settings.database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(url, echo=False, pool_pre_ping=True)


engine = _make_engine()
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async DB session per request.

    Commits on clean exit, rolls back on exception. Future API routes use
    this via the `DbSession` Annotated alias below.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_session)]
