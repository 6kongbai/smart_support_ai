import asyncio
import re
from typing import Any, Optional

from langchain_neo4j import Neo4jGraph
from langchain_neo4j.chains.graph_qa.cypher_utils import Schema, CypherQueryCorrector
from loguru import logger

from app.db.neo4j.client import neo4j_conf

# 匹配目标：移除 Schema 字符串中自动生成的、无关的 'CypherQuery' 节点定义
_CYPHER_QUERY_NODE_PATTERN = re.compile(
    r"^(- \*\*CypherQuery\*\*[\s\S]+?)(^Relationship properties|- \*)",
    re.MULTILINE
)


def _clean_schema_string(schema_str: str) -> str:
    """
    清理原始 Schema 字符串：
    1. 移除无关的 CypherQuery 节点。
    2. 替换花括号以防止 LangChain Prompt 注入冲突。
    """
    if not schema_str:
        return ""

    if "CypherQuery" in schema_str:
        schema_str = _CYPHER_QUERY_NODE_PATTERN.sub(r"\2", schema_str)

    # Neo4j schema 属性是 {prop: type}，与 PromptTemplate 的 {variable} 冲突
    return schema_str.replace("{", "[").replace("}", "]")


def _load_schema_sync() -> tuple[Optional[str], Optional[dict[str, Any]]]:
    """
    同步从 Neo4j 加载 schema，并返回（文本schema, 结构化schema）。
    出错时返回 (None, None)。
    """
    graph = Neo4jGraph(
        url=neo4j_conf["URI"],
        username=neo4j_conf["USERNAME"],
        password=neo4j_conf["PASSWORD"],
        database=neo4j_conf["DATABASE"]
    )

    schema_text = _clean_schema_string(graph.schema)
    structured = graph.structured_schema

    logger.info("Neo4j schema loaded successfully")
    return schema_text, structured


_GRAPH_SCHEMA: Optional[str] = None
_STRUCTURED_SCHEMA: Optional[dict[str, Any]] = None


def _loaded() -> None:
    """
    确保 schema 已加载到内存（线程安全 lazy-init）。
    若加载失败则抛 RuntimeError。
    """

    global _GRAPH_SCHEMA, _STRUCTURED_SCHEMA

    schema_text, structured = _load_schema_sync()
    if schema_text is None or structured is None:
        raise RuntimeError("Failed to load Neo4j schema. Please check your Neo4j connection configuration.")

    _GRAPH_SCHEMA = schema_text
    _STRUCTURED_SCHEMA = structured


_loaded()


def get_graph_schema() -> str:
    """
    获取 Neo4j 图数据库的 schema 文本。
    """
    return _GRAPH_SCHEMA


def get_structured_schema() -> dict[str, Any]:
    """
    获取 Neo4j 图数据库的结构化 schema。
    """
    return _STRUCTURED_SCHEMA


def get_corrector() -> CypherQueryCorrector:
    """
    获取 Cypher 查询校正器。
    """
    structured_schema = get_structured_schema()

    relationships = structured_schema.get("relationships") or []
    if not relationships:
        logger.warning("No relationships found in structured schema")

    schemas = [Schema(r["start"], r["type"], r["end"]) for r in relationships]
    return CypherQueryCorrector(schemas)
