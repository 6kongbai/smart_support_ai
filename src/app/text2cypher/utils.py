import re
from functools import cache
from typing import List, Iterator, Optional, Dict, Literal

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.vectorstores import VectorStoreRetriever

from app.db.milvus.client import get_milvus, retriever
from app.db.neo4j.client import get_async_session
from app.db.neo4j.utils import get_graph_schema, get_structured_schema
from app.llms.llm import get_router_model
from app.text2cypher.prompts import create_text2cypher_generation_prompt_template, \
    create_text2cypher_validation_prompt_template, create_text2cypher_correction_prompt_template
from app.text2cypher.types import ValidateCypherOutput, Property

WRITE_CLAUSES_REGEX = re.compile(
    r"\b(CREATE|DELETE|DETACH|SET|REMOVE|FOREACH|MERGE|DROP|CALL)\b",
    re.IGNORECASE | re.MULTILINE
)


def format_cypher(docs: List[Document]) -> Iterator[str]:
    """
    将 Document 列表格式化为 Few-Shot 字符串，并返回一个迭代器。
    """
    components = (
        f"Question: {doc.page_content}\nCypher: {doc.metadata.get('cypher', '')}"
        for doc in docs
    )

    # 必须使用 yield 来满足 LangChain 对流式接口的类型要求 (Iterator[str])
    yield "\n\n".join(components)


@cache
def _valid_props_by_label() -> Dict[str, dict[str, str]]:
    node_props = get_structured_schema().get("node_props", {})
    return {
        label: {p.get("property"): p.get("type") for p in props if "property" in p}
        for label, props in node_props.items()
    }


def should_validate_property(label: str, key: str) -> bool:
    return key in _valid_props_by_label().get(label, set())


def get_schema_type(
        label: str, key: str
) -> Literal["STRING", "INTEGER", "FLOAT", "BOOLEAN", "NULL"] | None:
    return _valid_props_by_label().get(label, {}).get(key, None)


async def check_value_exists_async(filter_item: Property) -> Optional[str]:
    """
    仅当操作符为 '=' 时，使用原生 AsyncSession 检查属性值是否存在。
    其他的操作符（IN, CONTAINS, >, < 等）一律跳过校验，避免误报。
    """

    if filter_item.operator != "=":
        return None

    expected_type = get_schema_type(filter_item.node_label, filter_item.property_key)
    final_value = filter_item.property_value

    # --- 类型对齐逻辑 (仅处理单值) ---
    if expected_type == "INTEGER" and isinstance(final_value, str):
        if final_value.isdigit():
            final_value = int(final_value)
        else:
            return f"Type Mismatch: Expected INTEGER for {filter_item.property_key}, got non-digit string."

    elif expected_type == "STRING" and isinstance(final_value, (int, float)):
        final_value = str(final_value)

    # --- 构建 Cypher (仅需处理 =) ---
    cypher_query = (
        f"MATCH (n:{filter_item.node_label}) "
        f"WHERE n.{filter_item.property_key} = $value "
        f"RETURN 1 LIMIT 1"
    )

    try:
        async with get_async_session() as session:
            result = await session.run(cypher_query, value=final_value)
            record = await result.peek()

            if not record:
                return (
                    f"可能存在幻觉或拼写错误：在数据库中未找到 "
                    f"{filter_item.node_label}.{filter_item.property_key} = {final_value} 的数据。"
                )
            return None

    except Exception as e:
        # 数据库连接等系统错误依然需要抛出或记录
        return f"DB Async Check Error: {str(e)}"


def get_cypher_generation_chain():
    text2cypher_prompt = create_text2cypher_generation_prompt_template().partial(
        schema=get_graph_schema()
    )

    context_prep_chain = {
        "examples": retriever | RunnableLambda(format_cypher),
        "question": RunnablePassthrough(),
    }

    return context_prep_chain | text2cypher_prompt | get_router_model() | StrOutputParser()


def get_validate_cypher_chain():
    prompt = create_text2cypher_validation_prompt_template().partial(
        schema=get_graph_schema()
    )
    llm = get_router_model()
    return prompt | llm.with_structured_output(ValidateCypherOutput)


def get_correct_cypher_chain():
    correction_cypher_prompt = create_text2cypher_correction_prompt_template().partial(
        schema=get_graph_schema()
    )
    llm = get_router_model()
    return correction_cypher_prompt | llm | StrOutputParser()
