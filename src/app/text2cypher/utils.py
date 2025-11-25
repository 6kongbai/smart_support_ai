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
    使用原生 AsyncSession 检查属性值是否存在。
    支持多种操作符处理。
    """

    # 1. 过滤不需要校验的操作符
    # 通常我们只关心精确匹配的实体是否存在，范围查询(>, <)通常不需要校验值是否存在于库中
    if filter_item.operator in [">", "<", ">=", "<="]:
        return None

    expected_type = get_schema_type(filter_item.node_label, filter_item.property_key)
    final_value = filter_item.property_value

    # --- 类型对齐逻辑 (处理单个值) ---
    # 注意：如果 operator 是 IN，final_value 可能是 list，需要特殊处理
    if filter_item.operator != "IN":
        if expected_type == "INTEGER" and isinstance(final_value, str):
            if final_value.isdigit():
                final_value = int(final_value)
            else:
                return f"Type Mismatch: Expected INTEGER for {filter_item.property_key}, got non-digit string."
        elif expected_type == "STRING" and isinstance(final_value, (int, float)):
            final_value = str(final_value)

    # --- 动态构建 Cypher ---
    # 我们只对 '=' 和 'IN' 做强校验，对模糊匹配做相应构建

    if filter_item.operator == "=":
        cypher_query = (
            f"MATCH (n:{filter_item.node_label}) "
            f"WHERE n.{filter_item.property_key} = $value "
            f"RETURN 1 LIMIT 1"
        )
    elif filter_item.operator == "IN":
        # 对于 IN，只要列表中有一个值存在即可，还是必须全部存在？
        # 通常校验逻辑是：只要库里没这个值，可能是幻觉。
        # 这里简化处理：检查是否有节点满足该 IN 条件
        cypher_query = (
            f"MATCH (n:{filter_item.node_label}) "
            f"WHERE n.{filter_item.property_key} IN $value "
            f"RETURN 1 LIMIT 1"
        )
    elif filter_item.operator in ["CONTAINS", "STARTS WITH", "ENDS WITH"]:
        # 模糊匹配校验
        op = filter_item.operator
        cypher_query = (
            f"MATCH (n:{filter_item.node_label}) "
            f"WHERE n.{filter_item.property_key} {op} $value "
            f"RETURN 1 LIMIT 1"
        )
    else:
        # 其他情况（如 <>）通常跳过校验
        return None

    try:
        async with get_async_session() as session:
            # 这里的 final_value 可能是单个值，也可能是列表（针对 IN）
            result = await session.run(cypher_query, value=final_value)
            record = await result.peek()

            if not record:
                # 针对不同操作符生成更友好的错误信息
                msg = f"Value validation failed for {filter_item.node_label}.{filter_item.property_key}"
                if filter_item.operator == "=":
                    msg += f" (Expected exact match: {final_value})"
                elif filter_item.operator == "IN":
                    msg += f" (Expected one of: {final_value})"
                else:
                    msg += f" (Criteria: {filter_item.operator} {final_value})"
                return msg

            return None

    except Exception as e:
        # 记录日志而不是直接抛出，以免打断整个链条，或者根据需求 raise
        return f"DB Check Error: {str(e)}"


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
