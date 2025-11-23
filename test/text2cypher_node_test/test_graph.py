import pytest

from app.text2cypher.builder import build_text2pycher_agent

@pytest.mark.asyncio(loop_scope="session")
async def test_graph():
    graph = build_text2pycher_agent()

    # 1. 准备输入：LangGraph 推荐直接使用普通字典
    inputs = {
        "question": "查一下商品ID是34的产品名称",
        "llm_validation": True
    }

    config = {"configurable": {"thread_id": "1"}}

    # 2. 关键修改：加上 await
    print("开始执行...")
    result = await graph.ainvoke(inputs, config)

    print("执行结果:")
    print(result)
