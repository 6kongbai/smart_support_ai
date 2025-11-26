import atexit
from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from typing import Callable, Generator, AsyncGenerator

from neo4j import GraphDatabase, Session, AsyncGraphDatabase, AsyncSession

from app.core.loader import load_yaml_config

neo4j_conf = load_yaml_config().get("NEO4J")

driver = GraphDatabase.driver(
    uri=neo4j_conf["URI"],
    auth=(neo4j_conf["USERNAME"], neo4j_conf["PASSWORD"]),
    max_connection_lifetime=3600,
    max_connection_pool_size=50,
    connection_acquisition_timeout=30,
)

async_driver = AsyncGraphDatabase.driver(
    uri=neo4j_conf["URI"],
    auth=(neo4j_conf["USERNAME"], neo4j_conf["PASSWORD"]),
    max_connection_lifetime=3600,
    max_connection_pool_size=50,
    connection_acquisition_timeout=30,
)

atexit.register(driver.close)


def _get_session() -> Session:
    """统一管理 session 创建，方便后续扩展."""
    return driver.session(database=neo4j_conf["DATABASE"])


async def _get_async_session() -> AsyncSession:
    return async_driver.session(database=neo4j_conf["DATABASE"])


def with_session(func: Callable):
    """
    为函数自动注入 Neo4j session。
    兼容普通函数
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        session = _get_session()
        try:
            return func(session, *args, **kwargs)
        finally:
            session.close()

    return wrapper


@contextmanager
def get_session():
    session: Session = _get_session()
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def get_async_session():
    session: AsyncSession = await _get_async_session()
    try:
        yield session
    finally:
        await session.close()


def with_async_session(func: Callable):
    """异步函数注入异步 session"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        session = await _get_async_session()
        try:
            return await func(session, *args, **kwargs)
        finally:
            await session.close()

    return wrapper


async def fast_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """异步 FastAPI 依赖注入"""
    session = await _get_async_session()
    try:
        yield session
    finally:
        await session.close()


def fast_get_session() -> Generator[Session, None, None]:
    """
    FastAPI 路由依赖注入:

    用法:
        @app.get("/")
        def handler(session: Session = Depends(get_neo4j_session)):
            ...
    """
    session = _get_session()
    try:
        yield session
    finally:
        session.close()
