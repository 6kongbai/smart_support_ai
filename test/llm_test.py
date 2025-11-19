
from app.graph.types import Router
from app.llms.llm import get_llm_by_name


def test_llm_load():
    llm = get_llm_by_name("qwen")  # 默认模型
    response = llm.invoke("你好")
    print(response)


def test_llm():
    print(get_llm_by_name().with_structured_output(Router))
