from functools import wraps
from typing import Callable, Generator

from langchain_neo4j import Neo4jGraph
from neo4j import GraphDatabase, Session, Driver

from app.core.loader import load_yaml_config

neo4j_conf = load_yaml_config().get("NEO4J")

driver = GraphDatabase.driver(
    uri=neo4j_conf["URI"],
    auth=(neo4j_conf["USERNAME"], neo4j_conf["PASSWORD"]),
    max_connection_lifetime=3600,
    max_connection_pool_size=50,
    connection_acquisition_timeout=30,
)


def get_neo4j_graph() -> Neo4jGraph:
    """
    创建并返回一个Neo4jGraph实例，使用配置文件中的设置。

    Returns:
        Neo4jGraph: 配置好的Neo4j图数据库连接实例
    """

    try:
        # 创建Neo4j图实例
        neo4j_graph = Neo4jGraph(
            url=neo4j_conf["URI"],
            username=neo4j_conf["USERNAME"],
            password=neo4j_conf["PASSWORD"],
            database=neo4j_conf["DATABASE"]
        )
        return neo4j_graph
    except Exception as e:
        # 创建driver失败
        raise e


def _get_session() -> Session:
    """统一管理 session 创建，方便后续扩展."""
    return driver.session(database=neo4j_conf["DATABASE"])


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


def get_neo4j_session() -> Generator[Session, None, None]:
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
