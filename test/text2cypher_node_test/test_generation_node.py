import asyncio

import pytest
from langgraph.types import Command  # 假设你用了 LangGraph 的 Command

from app.text2cypher.nodes import generation_cypher

# =====================
# 正向测试用例列表
# =====================
POSITIVE_TEST_CASES = [
    (
        "查一下商品ID是101的产品名称",
        "MATCH (p:Product) WHERE p.ProductID = 101 RETURN p.ProductName"
    ),
    (
        "查找联系人为'张三'的客户",
        "MATCH (c:Customer) WHERE c.ContactName = '张三' RETURN c.CustomerID"
    ),
    (
        "查询订单号为5001的订单详情和物流情况",
        "MATCH (o:Order) WHERE o.OrderID = 5001 RETURN o"
    ),
]


# =====================
# 测试函数
# =====================
@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("question,expected_cypher", POSITIVE_TEST_CASES)
async def test_generation_cypher_success(question, expected_cypher):
    """
    测试 Cypher 生成节点是否正确执行并返回 Command。
    由于配置了 session 级别的 loop，这里多次调用不会报 loop closed 错误。
    """

    # 1. 准备输入
    # 确保 state 的结构符合你的 GraphState 定义
    state = {"question": question}
    config = {"configurable": {"thread_id": "1"}}

    # 2. 执行节点
    # 注意：因为使用了 @cache，第二次调用时会复用第一次的连接，
    # 但因为 loop 没死，所以连接依然有效。
    result = await generation_cypher(state, config=config)

    # 3. 验证类型及跳转
    # 确保 result 是 Command 类型 (根据你的 import 调整)
    assert isinstance(result, Command)
    assert result.goto == "validate_cypher"

    # 4. 获取实际生成内容
    # 根据 Command 的结构获取 update 中的 cypher
    actual = result.update.get("cypher", "")

    print(actual)
