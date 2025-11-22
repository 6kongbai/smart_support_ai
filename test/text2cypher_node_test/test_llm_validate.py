import pytest
from langgraph.types import Command
from app.text2cypher.nodes import validate_cypher_with_llm
from app.text2cypher.types import Property
from app.text2cypher.utils import should_validate_property


def test_should_validate_property():
    p = Property(node_label='Product', property_key='ProductID', property_value='666666')
    print(should_validate_property("Product", "ProductID"))

# 你需要保证库里确实有 ProductID=101
POSITIVE_CASES = [
    (
        {
            "question": "查一下商品ID是101的产品名称",
            "cypher": "MATCH (p:Product) WHERE p.ProductID = 101 RETURN p.ProductName",
        },
        "__end__",
        0,
    )
]

# 你需要保证库里绝对没有 ProductID=999999
MAPPING_ERROR_CASES = [
    # --- 1. 整数类型 (Integer) 测试 ---
    (
        {
            "question": "查找供应商ID为999999的公司名称",
            # SupplierID 在 Schema 中是 INTEGER
            "cypher": "MATCH (s:Supplier) WHERE s.SupplierID = 999999 RETURN s.CompanyName",
        },
        "__end__",
        "Missing value mapping",
    ),
    (
        {
            "question": "查看ID为8888的分类下有哪些产品",
            # CategoryID 在 Schema 中是 INTEGER
            "cypher": "MATCH (c:Category {CategoryID: 8888})<-[:BELONGS_TO]-(p:Product) RETURN p.ProductName",
        },
        "__end__",
        "Missing value mapping",
    ),

    # --- 2. 字符串类型 (String) - ID 测试 ---
    (
        {
            "question": "查询客户ID为'NONEXISTENT'的联系方式",
            # CustomerID 在 Schema 中是 STRING
            "cypher": "MATCH (c:Customer) WHERE c.CustomerID = 'NONEXISTENT' RETURN c.Phone",
        },
        "__end__",
        "Missing value mapping",
    ),
    (
        {
            "question": "查看订单号为'ORD-999-XYZ'的发货状态",
            # OrderID 在 Schema 中是 STRING
            "cypher": "MATCH (o:Order) WHERE o.OrderID = 'ORD-999-XYZ' RETURN o.Status",
        },
        "__end__",
        "Missing value mapping",
    ),

    # --- 3. 字符串类型 (String) - 普通属性测试 ---
    (
        {
            "question": "列出所有位于'Atlantis'（亚特兰蒂斯）城市的客户",
            # City 在 Schema 中是 STRING，'Atlantis' 肯定不存在
            "cypher": "MATCH (c:Customer) WHERE c.City = 'Atlantis' RETURN c.ContactName",
        },
        "__end__",
        "Missing value mapping",
    ),
    (
        {
            "question": "查找名为'Unobtainium Widget'的产品价格",
            # ProductName 在 Schema 中是 STRING
            "cypher": "MATCH (p:Product) WHERE p.ProductName = 'Unobtainium Widget' RETURN p.UnitPrice",
        },
        "__end__",
        "Missing value mapping",
    ),

    # --- 4. 浮点数类型 (Float) 测试 ---
    (
        {
            "question": "查找单价正好是 99999.99 的产品",
            # UnitPrice 在 Schema 中是 FLOAT
            # 注意：这里测试你的验证器是否能处理 Float 类型的比较
            "cypher": "MATCH (p:Product) WHERE p.UnitPrice = 99999.99 RETURN p.ProductName",
        },
        "__end__",
        "Missing value mapping",
    ),

    # --- 5. 逻辑/关系过滤测试 (Integer) ---
    (
        {
            "question": "查找评分正好是 100 分的评论",
            # Rating 在 Schema 中是 INTEGER (通常是1-5分，100分肯定不存在)
            "cypher": "MATCH (r:Review) WHERE r.Rating = 100 RETURN r.ReviewText",
        },
        "__end__",
        "Missing value mapping",
    )
]

# schema 错误：稳定触发 correction_cypher
SCHEMA_ERROR_CASES = [
    (
        {
            "question": "查询订单号为5001的订单详情",
            "cypher": "MATCH (o:Order) WHERE o.OrderNo = 5001 RETURN o",
        },
        "correction_cypher",
        "Schema",  # errors里应有 schema/field 错误提示
    )
]


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("state, expected_goto, expected_err_len", POSITIVE_CASES)
async def test_validate_cypher_with_llm_success(state, expected_goto, expected_err_len):
    config = {"configurable": {"thread_id": "1"}}
    result = await validate_cypher_with_llm(state, config=config)

    assert isinstance(result, Command)
    assert result.goto == expected_goto
    assert result.update is None


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("state, expected_goto, expected_err_keyword", MAPPING_ERROR_CASES)
async def test_validate_cypher_with_llm_mapping_error(state, expected_goto, expected_err_keyword):
    config = {"configurable": {"thread_id": "1"}}
    result = await validate_cypher_with_llm(state, config=config)

    assert isinstance(result, Command)
    assert result.goto == expected_goto

    errors = result.update.get("errors", [])
    assert len(errors) > 0
    assert any(expected_err_keyword in e for e in errors), errors
    print("errors:", errors)


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("state, expected_goto, expected_err_keyword", SCHEMA_ERROR_CASES)
async def test_validate_cypher_with_llm_schema_error(state, expected_goto, expected_err_keyword):
    config = {"configurable": {"thread_id": "1"}}
    result = await validate_cypher_with_llm(state, config=config)

    assert isinstance(result, Command)
    assert result.goto == expected_goto

    errors = result.update.get("errors", [])
    assert len(errors) > 0
    assert any(expected_err_keyword in e for e in errors), errors
    print("errors:", errors)
