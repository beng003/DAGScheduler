import pytest
import logging
from server import app
from config.database import (
    AsyncSessionLocal,
    async_engine,
    Base,
    ASYNC_SQLALCHEMY_DATABASE_URL,
)

from sqlalchemy.ext.asyncio import AsyncSession

# from urllib.parse import quote_plus
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker,
from typing import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from collections.abc import AsyncIterable
from asgi_lifespan import LifespanManager
import os
# # 配置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")  # note: to scope as session the anyio backend
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """全局数据库初始化（整个测试会话只执行一次）"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print(f"\n创建所有表: {ASYNC_SQLALCHEMY_DATABASE_URL}")
    yield
    async with async_engine.begin() as conn:
        print(f"\n丢弃所有表: {ASYNC_SQLALCHEMY_DATABASE_URL}")
        await conn.run_sync(Base.metadata.drop_all)


# 定义 Pytest Fixture
@pytest.fixture(scope="session")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as current_db:
        yield current_db


@pytest.fixture(scope="session")
async def async_client() -> AsyncIterable[AsyncClient]:
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://localhost:9099"
        ) as ac:
            yield ac
