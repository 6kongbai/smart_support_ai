from langchain_milvus import Milvus
from pymilvus import MilvusClient

from app.core.loader import load_yaml_config
from app.llms.llm import get_embedding_model

conf = load_yaml_config().get("MILVUS")

client = MilvusClient(uri=conf["URI"])


def get_milvus() -> Milvus:
    return Milvus(
        embedding_function=get_embedding_model(),
        connection_args={"uri": conf["URI"]},
        index_params={"index_type": "FLAT", "metric_type": "COSINE"},
        collection_name="cypher"
    )


# vector_store = Milvus(
#     embedding_function=get_llm_by_name("embedding"),
#     connection_args={"uri": URI},
#     index_params={"index_type": "FLAT", "metric_type": "COSINE"},
#     collection_name="cypher"
# )
#
# retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 1})
