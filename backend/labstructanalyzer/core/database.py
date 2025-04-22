import os
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, Session
from sqlmodel.ext.asyncio.session import AsyncSession

async_engine = create_async_engine(os.getenv("DATABASE_URL"))
sync_engine = create_engine(os.getenv("DATABASE_URL"))


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(async_engine) as session:
        yield session


def get_sync_session() -> Generator[Session, None, None]:
    with Session(sync_engine) as session:
        yield session


async def close_db():
    await async_engine.dispose()


def close_sync_db():
    sync_engine.dispose()
