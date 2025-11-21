import pytest
from langchain_core.messages import HumanMessage, AIMessage

from app.graph.nodes import analyze_and_route_query


# 模拟 State 的辅助函数
def mock_state(current_input: str, history: list = None):
    """
    构建模拟状态。

    Args:
        current_input: 用户当前的输入
        history: (可选) 对话历史列表，格式为 [(Role, Content), ...]
                 Role: 'human' or 'ai'
    """
    messages = []

    # 1. 构建历史消息
    if history:
        for role, content in history:
            if role == 'human':
                messages.append(HumanMessage(content=content))
            elif role == 'ai':
                messages.append(AIMessage(content=content))

    # 2. 添加当前用户输入
    messages.append(HumanMessage(content=current_input))

    return {"messages": messages}


# 定义测试数据结构:
# (当前输入, 历史记录[(role, content)], 预期路由目标, 备注说明)

TEST_CASES = [
    # ==========================================
    # 1. general-query (闲聊/通用)
    # ==========================================
    (
        "你好，你是真人吗？",
        [],
        "general-query",
        "通用闲聊，不涉及业务"
    ),
    (
        "今天天气怎么样？",
        [],
        "general-query",
        "非电商业务领域的问题"
    ),

    # ==========================================
    # 2. graphrag-query (参数齐全/政策查询/上下文继承)
    # ==========================================
    # 2.1 显式参数齐全
    (
        "帮我查一下订单号 20230001 的状态",
        [],
        "graphrag-query",
        "参数齐全(订单号)，可直接执行"
    ),
    (
        "iPhone 15 Pro Max 256G 现在多少钱？",
        [],
        "graphrag-query",
        "参数齐全(具体商品)，可直接查询"
    ),

    # 2.2 通用政策 (不需要参数)
    (
        "你们支持七天无理由退货吗？",
        [],
        "graphrag-query",
        "通用政策查询，无需特定参数"
    ),
    (
        "怎么连接家里的WiFi？",
        [],
        "graphrag-query",
        "通用教程/技术支持，无需特定参数"
    ),

    # 2.3 上下文继承 (Context Inheritance) - 关键测试点！
    (
        "它现在的物流到哪了？",
        [("human", "我刚才买了个戴森吹风机，订单号是 ORDER_999")],
        "graphrag-query",
        "依靠上文'订单号'，当前输入虽无参数但意图完整"
    ),
    (
        "有白色的吗？",
        [("human", "我想买那个 Sony XM5 耳机"), ("ai", "好的，为您查询到库存充足。")],
        "graphrag-query",
        "依靠上文'Sony XM5'，查询具体规格"
    ),

    # ==========================================
    # 3. additional-query (参数缺失/指代不明)
    # ==========================================
    (
        "帮我查下订单",
        [],
        "additional-query",
        "意图明确但缺失订单号，且无历史记录"
    ),
    (
        "这个多少钱？",
        [],
        "additional-query",
        "指代不明('这个')，且无历史上下文"
    ),
    (
        "我想退货",
        [("human", "你好"), ("ai", "你好，有什么可以帮您？")],
        "additional-query",
        "虽有历史但历史中未包含具体订单信息，无法执行退货"
    ),

    # ==========================================
    # 4. image-query (图片/文件引用)
    # ==========================================
    (
        "请看上面这张图，我的屏幕报错了",
        [],  # 假设系统在其他地方处理了图片上传，这里只测文本路由
        "image-query",
        "明确引用了图片内容"
    ),
    (
        "按照这个文档里的清单发货",
        [],
        "file-query",  # 如果你的 Prompt 区分了 file 和 image，否则也是 image-query
        "明确引用了文件内容"
    ),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("user_input, history, expected_jump, note", TEST_CASES)
async def test_router_logic(user_input, history, expected_jump, note):
    """
    测试路由器的意图分类逻辑
    """
    # 1. 构造 State
    state = mock_state(user_input, history)
    config = {} # 你的 RunnableConfig，如果需要 mock 可以传空字典

    print(f"\n---------------------------------------------------")
    print(f"测试场景: {note}")
    print(f"用户输入: {user_input}")
    print(f"上下文数: {len(history) if history else 0}")

    # 2. 执行被测函数
    # 注意：这里假设 analyze_and_route_query 是异步的
    result = await analyze_and_route_query(state, config=config)

    # 3. 获取结果
    actual_jump = result.get("jump_to")
    reasoning = result.get("reasoning")

    print(f"LLM 思考: {reasoning}")
    print(f"路由结果: {actual_jump} (预期: {expected_jump})")

    # 4. 断言验证
    assert actual_jump == expected_jump, \
        f"路由错误！\n输入: {user_input}\n历史: {history}\n预期: {expected_jump}\n实际: {actual_jump}\n分析: {reasoning}"

    # 5. 额外的鲁棒性检查 (可选)
    if actual_jump == "additional-query":
        # 如果是 missing info，reasoning 里最好能提到缺什么
        keywords = ["缺少", "提供", "missing", "provide", "specify", "未提供"]
        assert any(k in reasoning for k in keywords), "additional-query 的 reasoning 应该说明缺失了什么信息"