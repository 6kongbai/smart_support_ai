from langchain_core.runnables import RunnableLambda

from app.db.milvus.client import client, get_milvus
from app.db.milvus.milvus_init import init_milvus, clear_milvus
from app.db.milvus.utils import format_cypher


def test_milvus_init():
    init_milvus()


def test_clear_milvus():
    clear_milvus()


def test_milvus_search():
    print(client.list_collections())
    print(client.has_collection("cypher"))


def test_retriever():
    vector_stores = get_milvus()
    retriever = vector_stores.as_retriever(search_type="mmr", search_kwargs={"k": 3})
    chain = retriever | RunnableLambda(format_cypher)
    print(chain.invoke("查一下物流单号SF123"))
