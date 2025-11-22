from langchain_core.example_selectors import MaxMarginalRelevanceExampleSelector

from app.db.milvus.client import client, get_milvus
from app.db.milvus.milvus_init import init_milvus, clear_milvus


def test_milvus_init():
    init_milvus()


def test_clear_milvus():
    clear_milvus()


def test_milvus_search():
    print(client.list_collections())
    print(client.has_collection("cypher"))


def test_retriever():
    vectorstore = get_milvus()

    example_selector = MaxMarginalRelevanceExampleSelector(
        vectorstore=vectorstore,
        k=2,
    )

    # 这一步不是错误，只是查询时传入的键名为 "question"
    example = example_selector.select_examples({"question": "查一下物流单号SF123"})

    # retriever = vector_stores.as_retriever(search_type="mmr", search_kwargs={"k": 3})
    # chain = retriever | RunnableLambda(format_cypher)
    # print(chain.invoke("查一下物流单号SF123"))
