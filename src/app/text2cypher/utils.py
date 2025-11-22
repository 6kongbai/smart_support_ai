import re
from functools import cache
from typing import List, Iterator, Optional, Dict, Set

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from app.db.milvus.client import get_milvus
from app.db.neo4j.client import get_async_session
from app.db.neo4j.utils import get_graph_schema, get_structured_schema
from app.llms.llm import get_router_model, get_chat_model
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
def _valid_props_by_label() -> Dict[str, Set[str]]:
    node_props = get_structured_schema().get("node_props", {})
    return {
        label: {p.get("property") for p in props if "property" in p}
        for label, props in node_props.items()
    }


def should_validate_property(label: str, key: str) -> bool:
    return key in _valid_props_by_label().get(label, set())


async def check_value_exists_async(filter_item: Property) -> Optional[str]:
    """
    使用原生 AsyncSession 检查属性值是否存在。
    """
    cypher_query = (
        f"MATCH (n:`{filter_item.node_label}`) "
        f"WHERE n.{filter_item.property_key} = $value "
        f"RETURN 1 LIMIT 1"
    )

    try:
        async with get_async_session() as session:
            result = await session.run(cypher_query, value=filter_item.property_value)
            record = await result.peek()
            if not record:
                return (
                    f"Missing value mapping for {filter_item.node_label} "
                    f"on property {filter_item.property_key} with value '{filter_item.property_value}'"
                )
            return None

    except Exception as e:
        raise e


def get_cypher_generation_chain():
    retriever = get_milvus().as_retriever(search_type="mmr")
    text2cypher_prompt = create_text2cypher_generation_prompt_template().partial(
        schema=get_graph_schema()
    )

    context_prep_chain = {
        "examples": retriever | RunnableLambda(format_cypher),
        "question": RunnablePassthrough(),
    }

    return context_prep_chain | text2cypher_prompt | get_chat_model() | StrOutputParser()


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
