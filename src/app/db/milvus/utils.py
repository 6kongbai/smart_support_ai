from typing import List, Iterator

from langchain_core.documents import Document
from loguru import logger

from app.db.milvus.client import client


def remove_milvus_collection(collection_name: str):
    if client.has_collection(collection_name):
        try:
            client.drop_collection(collection_name)
            logger.info(f"Collection '{collection_name}' dropped.")
        except Exception as e:
            logger.error(f"Error dropping collection '{collection_name}': {e}")
    else:
        logger.error(f"Collection '{collection_name}' does not exist.")


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
