import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

engine = create_async_engine(os.getenv("DATABASE_URL"), pool_pre_ping=True)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session


async def close_db():
    await engine.dispose()
