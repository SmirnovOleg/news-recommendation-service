from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database.models import Base


class AsyncSQLiteDBService:
    def __init__(self) -> None:
        self.engine: Any = None
        self.async_session: Any = None

    async def init(self) -> None:
        self.engine = create_async_engine(settings.sqlite_url, echo=True)
        self.async_session = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def create_session(self) -> AsyncIterator[Any]:
        new_session = self.async_session()
        try:
            yield new_session
            await new_session.commit()
        except Exception:  # pragma: no cover
            await new_session.rollback()
            raise
        finally:
            await new_session.close()

    async def get_session(self) -> AsyncSession:
        async with self.create_session() as session:
            yield session


db = AsyncSQLiteDBService()
