import pytest
from langchain_core.messages import HumanMessage

from app.graph.nodes import analyze_and_route_query, respond_to_general_query, get_additional_info
from app.graph.types import State


async def test_analyze_and_route_query_simple():
    fake_state = State(messages=[{"role": "user", "content": "你好"}])
    fake_config = {}
    result = await analyze_and_route_query(fake_state, config=fake_config)
    print(result)


async def test_respond_to_general_query():
    fake_state = State(
        messages=[{"role": "user", "content": "你好"}],
        jump_to="general-query",
        cause="用户输入了普通问题",
    )
    fake_config = {}
    state = await respond_to_general_query(fake_state, config=fake_config)
    print(state)

async def test_get_additional_info():
    fake_state = State(
        messages=[{"role": "user", "content": "你好"}],
        jump_to="additional-query",
        cause="用户输入了普通问题",
    )
    fake_config = {}
    state = await get_additional_info(fake_state, config=fake_config)
    print(state)


def mock_state(user_input: str):
    return {
        "messages": [HumanMessage(content=user_input)],
        # 如果 get_additional_info 依赖其他字段，在这里补充
        # "missing_info_reason": ...
    }


# 定义测试用例数据：(用户输入, 预期结果类型)
# 类型说明:
#   "block": 应该被护栏拦截
#   "pass": 应该通过护栏并进行追问
TEST_CASES = [
    # --- 场景 1: 明确越界 (应该拦截) ---
    ("亲，你们这有耐克的跑鞋卖吗？42码的。", "block"),
    ("今天北京天气怎么样？适合出去玩吗？", "block"),
    ("帮我写个贪吃蛇的Python代码", "block"),

    # --- 场景 2: 正常业务 (应该放行并追问) ---
    ("我想买个智能开关", "pass"),
    ("家里太暗了，有没有那种能让屋里变亮亮的东西？", "pass"),  # 语义理解测试

    # --- 场景 3: 社交闲聊 (应该放行并礼貌回复) ---
    ("你好呀，在吗？", "pass"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("user_input, expected_type", TEST_CASES)
async def test_guardrail_logic(user_input, expected_type):
    """
    参数化测试：验证安全护栏是否能正确区分业务和非业务问题
    """
    # 1. 准备状态
    state = mock_state(user_input)
    config = {}

    # 2. 执行函数 (调用真实的 LLM)
    print(f"\n正在测试: {user_input} ...")
    result = await get_additional_info(state, config=config)

    # 3. 获取回复内容
    assert "messages" in result
    response_msg = result["messages"][0]
    content = response_msg.content

    print(f"系统回复: {content}")

    # 4. 断言验证
    # 我们在 get_additional_info 代码里定义的拒绝话术包含 "抱歉" 或 "别家"
    is_refusal = "抱歉" in content or "别家" in content

    if expected_type == "block":
        assert is_refusal is True, \
            f"预期被拦截，但系统放行了。\n输入: {user_input}\n回复: {content}"
    else:
        assert is_refusal is False, \
            f"预期被放行，但系统拦截了。\n输入: {user_input}\n回复: {content}"