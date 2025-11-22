import re
from functools import cache
from typing import Any

from langchain_neo4j import Neo4jGraph
from langchain_neo4j.chains.graph_qa.cypher_utils import Schema, CypherQueryCorrector

from app.db.neo4j.client import get_neo4j_graph

# 匹配目标：移除 Schema 字符串中自动生成的、无关的 'CypherQuery' 节点定义
CYPHER_QUERY_NODE_PATTERN = re.compile(
    r"^(- \*\*CypherQuery\*\*[\s\S]+?)(^Relationship properties|- \*)",
    re.MULTILINE
)


def _clean_schema_string(schema_str: str) -> str:
    """
    清理原始 Schema 字符串：
    1. 移除无关的 CypherQuery 节点。
    2. 替换花括号以防止 LangChain Prompt 注入冲突。
    """
    # 移除干扰节点
    if "CypherQuery" in schema_str:
        schema_str = CYPHER_QUERY_NODE_PATTERN.sub(r"\2", schema_str)

    # 替换花括号：Neo4j schema 包含 {prop: type}，但这会与 PromptTemplate 的 {variable} 冲突
    # 将 { } 替换为 [ ] 是业界通用的做法
    return schema_str.replace("{", "[").replace("}", "]")


@cache
def get_graph_schema() -> str:
    """
    获取并缓存格式化后的文本 Schema。
    用于注入到 Prompt Template 中。
    """
    try:
        graph: Neo4jGraph = get_neo4j_graph()
        # 注意：graph.schema 是一个属性，获取它可能会触发一次对 Neo4j 的查询（取决于 LangChain 版本）
        raw_schema = graph.schema
        return _clean_schema_string(raw_schema)
    except Exception as e:
        # 在这里可以添加日志 logging.error(f"获取 Schema 失败: {e}")
        raise e


@cache
def get_structured_schema() -> dict[str, Any]:
    """
    获取并缓存结构化的 Schema 列表。
    仅用于 CypherQueryCorrector，不直接用于 Prompt。
    """
    graph = get_neo4j_graph()
    return graph.structured_schema


@cache
def get_corrector() -> CypherQueryCorrector:
    """
    获取全局单例的 CypherQueryCorrector。
    初始化 Corrector 开销较大，必须缓存。
    """

    structured_schema = get_structured_schema()
    schemas = [
        Schema(el["start"], el["type"], el["end"])
        for el in structured_schema.get("relationships", [])
    ]
    return CypherQueryCorrector(schemas)
