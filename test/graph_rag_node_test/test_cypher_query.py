from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from app.db.milvus.client import get_milvus
from app.db.neo4j.utils import get_graph_schema
from app.text2cypher.utils import create_text2cypher_generation_prompt_template, format_cypher
from app.llms.llm import get_chat_model


def test_chain():
    retriever = get_milvus().as_retriever(search_type="mmr")
    text2cypher_prompt = create_text2cypher_generation_prompt_template().partial(
        schema=get_graph_schema()
    )

    context_prep_chain = {
        "examples": retriever | RunnableLambda(format_cypher),
        "question": RunnablePassthrough(),
    }

    cypher_chain = context_prep_chain | text2cypher_prompt | get_chat_model() | StrOutputParser()
    print(cypher_chain.invoke("查一下物流单号SF123"))
