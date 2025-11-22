import pytest
from langchain_core.prompts import ChatPromptTemplate

from app.db.neo4j.client import get_async_session
from app.db.neo4j.utils import get_graph_schema, get_structured_schema
from app.llms.llm import get_chat_model, get_router_model
from app.text2cypher.types import ValidateCypherOutput
from app.text2cypher.utils import create_text2cypher_validation_prompt_template


async def test_session():
    cypher = (
        f"MATCH (n:`Product`) "
        f"ERE toLower(n.`ProductName`) = toLower($value) "
        f"RETURN 1 LIMIT 1"
    )
    async with get_async_session() as session:
        # 优雅的单行查询
        result = await session.run("EXPLAIN " + cypher, value="灯")
        # 如果 peek 不到记录，说明不存在
        res = await result.consume()
        print("res", res)


def test_get_schema():
    node_props_schema = get_structured_schema().get("node_props", {})
    label_schema = node_props_schema.get("Product")
    print()
    print(label_schema)
    target_prop_def = next(
        (p for p in label_schema if p["property"] == "ProductID"),
        None
    )
    print(target_prop_def["type"])


validation_prompt_template = create_text2cypher_validation_prompt_template()


@pytest.fixture(scope="session")
def cypher_validation_chain():
    """初始化验证链，绑定新的 ValidateCypherOutput 结构"""
    chain = validation_prompt_template | get_router_model().with_structured_output(
        ValidateCypherOutput
    )
    return chain


# ==========================================
# 2. 正向测试用例 (Expected Success)
# ==========================================

POSITIVE_TEST_CASES = [
    (
        "查一下商品ID是101的产品名称",
        "MATCH (p:Product) WHERE p.ProductID = 101 RETURN p.ProductName",
        [{"node_label": "Product", "property_key": "ProductID", "property_value": "101"}]
    ),
    (
        "查找联系人为'张三'的客户",
        "MATCH (c:Customer) WHERE c.ContactName = '张三' RETURN c.CustomerID",
        [{"node_label": "Customer", "property_key": "ContactName", "property_value": "张三"}]
    ),
]


@pytest.mark.parametrize("question, cypher, expected_filters", POSITIVE_TEST_CASES)
def test_cypher_validation_success(cypher_validation_chain, question, cypher, expected_filters):
    """测试合法的 Cypher 语句，预期 errors 为空，且能提取出 filters"""

    result = cypher_validation_chain.invoke({
        "question": question,
        "schema": get_graph_schema(),
        "cypher": cypher,
    })

    # --- 关键断言变化 ---

    # 1. 断言 errors 列表必须为空 (None 或 空列表)
    assert not result.errors, \
        f"Expected valid Cypher, but found errors: {result.errors}\nQuestion: {question}\nCypher: {cypher}"

    # 2. 验证过滤器提取是否准确 (可选，但推荐)
    if expected_filters:
        assert result.filters is not None, "Expected filters to be found but got None"
        # 简单验证提取到的属性数量
        assert len(result.filters) == len(expected_filters)

        # 验证第一个过滤器的关键值
        first_filter = result.filters[0]
        assert first_filter.node_label == expected_filters[0]["node_label"]
        assert first_filter.property_key == expected_filters[0]["property_key"]
        assert first_filter.property_value == str(expected_filters[0]["property_value"])

    print(f"\n✅ [SUCCESS] Passed: {question}")


# ==========================================
# 3. 负向测试用例 (Expected Failure)
# ==========================================
# 这些测试用来确保您的 AI 真的能通过 Schema 发现错误
# 比如：查询不存在的属性，或者拼写错误的 Label

NEGATIVE_TEST_CASES = [
    (
        "查一下不存在的属性UserAge",
        # 错误点：Customer 表里没有 Age 属性 (假设 Schema 中没有)
        "MATCH (c:Customer) WHERE c.Age = 30 RETURN c.ContactName",
        "Age"  # 预期错误信息中包含的关键词
    ),
    (
        "错误的节点标签",
        # 错误点：Schema 里没有 'Client' 这个 Label，只有 'Customer'
        "MATCH (c:Client) WHERE c.Name = '张三' RETURN c.id",
        "Client"  # 预期错误信息中包含的关键词
    )
]


@pytest.mark.parametrize("question, cypher, expected_error_keyword", NEGATIVE_TEST_CASES)
def test_cypher_validation_failure(cypher_validation_chain, question, cypher, expected_error_keyword):
    """测试错误的 Cypher 语句，预期 errors 列表中包含错误信息"""

    result = cypher_validation_chain.invoke({
        "question": question,
        "schema": get_graph_schema(),
        "cypher": cypher,
    })
    print(result.filters)
    # 1. 断言 errors 列表不为空
    assert result.errors, \
        f"Expected errors for invalid Cypher, but got valid result.\nCypher: {cypher}"

    # 2. 验证错误信息是否包含关键点 (模糊匹配)
    # 将所有错误信息合并成一个字符串进行检查
    all_errors_text = " ".join(result.errors)
    assert expected_error_keyword in all_errors_text, \
        f"Expected error message to contain '{expected_error_keyword}', but got: {result.errors}"

    print(f"\n🛡️ [CAUGHT] Correctly identified error in: {cypher}")
    print(f"   Reason: {result.errors}")
