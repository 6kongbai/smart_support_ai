from functools import cache

from langchain_milvus import Milvus

from app.core.loader import load_yaml_config
from app.llms.llm import get_embedding_model

conf = load_yaml_config().get("MILVUS")


@cache
def get_milvus() -> Milvus:
    return Milvus(
        embedding_function=get_embedding_model(),
        connection_args={"uri": conf["URI"]},
        index_params={"index_type": "FLAT", "metric_type": "COSINE"},
        collection_name="cypher"
    )

