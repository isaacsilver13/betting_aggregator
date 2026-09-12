from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings
from app.storage.models import Base


def create_engine(settings: Settings) -> AsyncEngine:
    connect_args = {}
    if settings.database_url.startswith("postgresql+asyncpg"):
        # Neon (and other PgBouncer-fronted Postgres) run pooled connections
        # in transaction mode, which is incompatible with asyncpg's default
        # server-side prepared statement caching.
        connect_args["statement_cache_size"] = 0
    return create_async_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session