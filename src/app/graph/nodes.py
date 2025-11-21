from typing import cast, Dict, List

from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from app.db.neo4j.utils import get_graph_schema
from app.graph.state import OverallStates, InputState, OutputState
from app.graph.types import Router, JumpTo, GuardrailsOutput

from app.llms.llm import get_chat_model, get_router_model
from app.prompts.template import apply_prompt_template


async def analyze_and_route_query(
        state: InputState, *, config: RunnableConfig
) -> dict[str, JumpTo | str]:
    """
    Analyze the user query and determine the next routing step.
    
    This function uses a language model with structured output to classify
    the intent of the user's query and decide which part of the workflow
    should handle it next.

    Args:
        state (State): The current state containing conversation history.
        config (RunnableConfig): Configuration for the language model.

    Returns:
        dict[str, JumpTo | str]: A dictionary containing the next jump target
                                 and the reason for that decision.
    """
    # TODO 硬路由到文件和图片
    messages = apply_prompt_template("intent_router", state)

    # Use structured output to determine the intent and next step
    response = cast(
        Router,
        await get_router_model()
        .with_structured_output(Router)
        .ainvoke(messages)
    )

    return {
        "jump_to": response.next,
        "reasoning": response.reasoning,
    }


async def respond_to_general_query(
        state: OverallStates, *, config: RunnableConfig
) -> Dict[str, List[BaseMessage]]:
    """生成对一般查询的响应，完全基于大模型，不会触发任何外部服务的调用，包括自定义工具、知识库查询等。

    当路由器将查询分类为一般问题时，将调用此节点。

    Args:
        state (AgentState): 当前代理状态，包括对话历史和路由逻辑。
        config (RunnableConfig): 用于配置响应生成的模型。

    Returns:
        Dict[str, List[BaseMessage]]: 包含messages键的字典，其中包含生成的响应。
    """

    messages = apply_prompt_template("general_query", state)
    response = await get_chat_model().ainvoke(messages)

    return {"messages": [response]}


async def get_additional_info(
        state: OverallStates, *, config: RunnableConfig
) -> Dict[str, List[BaseMessage]]:
    """生成一个响应，要求用户提供更多信息。

    当路由确定需要从用户那里获取更多信息时，将调用此函数。

    Args:
        state (AgentState): 当前代理状态，包括对话历史和路由逻辑。
        config (RunnableConfig): 用于配置响应生成的模型。

    Returns:
        Dict[str, List[BaseMessage]]: 包含'messages'键的字典，其中包含生成的响应。
    """
    # 首先连接 Neo4j 图数据库
    graph_schema = get_graph_schema()
    # 定义电商经营范围
    scope_description = """
    个人电商经营范围：智能家居产品，包括但不限于：
    - 智能照明（灯泡、灯带、开关）
    - 智能安防（摄像头、门锁、传感器）
    - 智能控制（温控器、遥控器、集线器）
    - 智能音箱（语音助手、音响）
    - 智能厨电（电饭煲、冰箱、洗碗机）
    - 智能清洁（扫地机器人、洗衣机）

    不包含：服装、鞋类、体育用品、化妆品、食品等非智能家居产品。
    """
    # 第一步：安全护栏检查(GuardrailCheck)
    messages = apply_prompt_template(
        "safe_guardrail",
        state,
        scope_context=scope_description,
        graph_context=graph_schema
    )
    # TODO 测试messages中的调用
    guard_result = cast(
        GuardrailsOutput,
        await get_router_model()
        .with_structured_output(GuardrailsOutput)
        .ainvoke(messages)
    )

    # 2. 根据决策行动
    if guard_result.decision == "continue":
        ask_messages = apply_prompt_template("get_additional", state)
        response = await get_chat_model().ainvoke(ask_messages)
        return {"messages": [response]}
    else:
        return {"messages": [AIMessage(content="抱歉，我家暂时没有这方面的商品，可以在别家看看哦~")]}


async def create_research_plan(
        state: OverallStates, *, config: RunnableConfig
) -> Dict[str, List[str] | str]:
    """通过查询本地知识库回答客户问题，执行任务分解，创建分布查询计划。

    Args:
        state (AgentState): 当前代理状态，包括对话历史。
        config (RunnableConfig): 用于配置计划生成的模型。

    Returns:
        Dict[str, List[str] | str]: 包含'steps'键的字典，其中包含研究步骤列表。
    """
    pass
