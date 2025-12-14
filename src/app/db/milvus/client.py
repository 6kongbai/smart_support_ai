from langchain_milvus import Milvus

from app.core.loader import load_yaml_config
from app.llms.llm import get_embedding_model

conf = load_yaml_config().get("MILVUS")


def get_milvus() -> Milvus:
    return Milvus(
        embedding_function=get_embedding_model(),
        connection_args={"uri": conf["URI"], "token": conf["TOKEN"]},
        collection_name="cypher",
    )




if __name__ == '__main__':
    print(get_milvus().as_retriever(search_type="mmr"))
