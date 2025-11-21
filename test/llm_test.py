
from app.graph.types import Router
from app.llms.llm import get_chat_model


def test_llm_load():
    llm = get_chat_model()  # 默认模型
    response = llm.invoke("你好")
    print(response)


def test_llm():
    print(get_chat_model().with_structured_output(Router))
