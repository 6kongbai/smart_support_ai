from app.graph.types import Router
from app.llms.llm import get_function_call_model


def test_llm_load():
    llm = get_function_call_model()  # 默认模型
    response = llm.invoke("你好")
    print(response)


def test_llm():
    print(get_function_call_model().with_structured_output(Router))


