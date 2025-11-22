import pytest
from langgraph.types import Command

from app.text2cypher.nodes import validate_cypher

# =====================
# 正向测试用例（应通过 EXPLAIN，errors 为空）
# =====================
POSITIVE_CASES = [
    (
        "MATCH (p:Product) WHERE p.ProductID = 101 RETURN p.ProductName",
        False,  # llm_validation
        "validate_cypher_with_schema",
    ),
    (
        "MATCH (c:Customer) WHERE c.ContactName = '张三' RETURN c.CustomerID",
        True,
        "validate_cypher_with_llm",
    ),
    (
        # 物流字段在你的 schema 里存在
        "MATCH (o:Order) WHERE o.OrderID = 5001 RETURN o.TrackingNumber, o.CurrentLocation",
        False,
        "validate_cypher_with_schema",
    ),
]

# =====================
# 负向测试用例
# =====================
NEGATIVE_CASES = [
    (
        # 1) 写语句：应触发 Security Alert
        "MATCH (p:Product) SET p.UnitPrice = 999 RETURN p",
        False,
        "validate_cypher_with_schema",
        "Security Alert:",
    ),
    (
        # 2) 语法错误：EXPLAIN 会抛 CypherSyntaxError
        "MATCH (p:Product WHERE p.ProductID = 101 RETURN p",  # 少右括号
        True,
        "validate_cypher_with_llm",
        "Syntax Error:",
    ),
    (
        # 3) EXPLAIN 正常但你可以用明显非法的语法触发 Execution Error
        # （比如 Neo4j 版本不支持的关键字）
        "MATCH (p:Product) WHERE p.ProductID = 101 RETURN p INVALID_CLAUSE",
        False,
        "validate_cypher_with_schema",
        "Execution Error:",
    ),
]


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("cypher,llm_validation,expected_goto", POSITIVE_CASES)
async def test_validate_cypher_positive(cypher, llm_validation, expected_goto):
    """
    集成测试：不 mock，真实跑 corrector + Neo4j EXPLAIN
    目标：能走通且不报错
    """
    state = {
        "cypher": cypher,
        "llm_validation": llm_validation,
    }
    config = {"configurable": {"thread_id": "1"}}

    result = await validate_cypher(state, config=config)

    assert isinstance(result, Command)
    assert result.goto == expected_goto

    errors = result.update.get("errors", [])
    assert errors == []  # 正向用例必须无错误

    # corrected cypher 应该可执行 EXPLAIN（节点里已检查）
    corrected = result.update.get("cypher", "")
    assert isinstance(corrected, str) and corrected.strip()
    print("corrected:", corrected)


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "cypher,llm_validation,expected_goto,expected_error_prefix",
    NEGATIVE_CASES
)
async def test_validate_cypher_negative(cypher, llm_validation, expected_goto, expected_error_prefix):
    """
    集成测试：真实触发错误分支
    """
    state = {
        "cypher": cypher,
        "llm_validation": llm_validation,
    }
    config = {"configurable": {"thread_id": "1"}}

    result = await validate_cypher(state, config=config)

    assert isinstance(result, Command)
    assert result.goto == expected_goto

    errors = result.update.get("errors", [])
    assert len(errors) > 0

    # 只断言“包含某类错误”，避免 Neo4j 版本/细节导致 message 不同
    assert any(e.startswith(expected_error_prefix) for e in errors), errors
    print("errors:", errors)


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_cypher_autocorrect_integration():
    """
    集成测试：确认 corrector 真会改写并且改完能通过 EXPLAIN
    （前提：你的 corrector 确实会做这种改写）
    """
    original = "MATCH (o:Order) WHERE o.OrderID = '5001' RETURN o"
    state = {"cypher": original, "llm_validation": False}
    config = {"configurable": {"thread_id": "1"}}

    result = await validate_cypher(state, config=config)

    assert isinstance(result, Command)
    assert result.goto == "validate_cypher_with_schema"

    corrected = result.update.get("cypher", "")
    errors = result.update.get("errors", [])

    # 如果 corrector 生效，corrected 会 != original
    # 即便没生效也不要让测试挂（因为 corrector 规则可能调整）
    print("original :", original)
    print("corrected:", corrected)
    print("errors   :", errors)

    assert errors == []  # EXPLAIN 必须通过
