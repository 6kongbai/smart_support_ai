from typing import cast, Dict, List, Literal

from langchain_core.messages import BaseMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from loguru import logger

from app.graph.prompts import CHECK_HALLUCINATIONS
from app.graph.state import OverallState, InputState
from app.graph.types import Router, JumpTo, GuardrailsOutput, GradeHallucinations
from app.graph.utils import get_guardrail_check_chain, get_contextualize_question_chain
from app.graphrag.builder import build_graph_rag_agent
from app.llms.llm import get_chat_model, get_router_model
from app.prompts.template import apply_prompt_template


async def analyze_and_route_query(
        state: InputState, *, config: RunnableConfig
) -> Dict[str, JumpTo | str]:
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
        .ainvoke(messages, config=config)
    )

    return {"reasoning": response.reasoning, "next": response.next}


async def respond_to_general_query(
        state: OverallState, *, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    """生成对一般查询的响应，完全基于大模型，不会触发任何外部服务的调用，包括自定义工具、知识库查询等。

    当路由器将查询分类为一般问题时，将调用此节点。

    Args:
        state (AgentState): 当前代理状态，包括对话历史和路由逻辑。
        config (RunnableConfig): 用于配置响应生成的模型。

    Returns:
        Dict[str, List[BaseMessage]]: 包含messages键的字典，其中包含生成的响应。
    """
    thread_id = config.get("configurable", {}).get("thread_id", None)
    log = logger.bind(thread_id=thread_id)

    log.info(">> LLM一般回应")

    messages = apply_prompt_template("general_query", state)
    response = await get_chat_model().ainvoke(messages, config=config)

    return Command(
        goto="__end__",
        update={"messages": [response]},
    )


async def get_additional_info(
        state: OverallState, *, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    """生成一个响应，要求用户提供更多信息。

    当路由确定需要从用户那里获取更多信息时，将调用此函数。

    Args:
        state (AgentState): 当前代理状态，包括对话历史和路由逻辑。
        config (RunnableConfig): 用于配置响应生成的模型。

    Returns:
        Dict[str, List[BaseMessage]]: 包含'messages'键的字典，其中包含生成的响应。
    """
    thread_id = config.get("configurable", {}).get("thread_id", None)
    log = logger.bind(thread_id=thread_id)

    # 第一步：安全护栏检查(GuardrailCheck)
    guardrail_check_chain = get_guardrail_check_chain()
    guard_result: GuardrailsOutput = await guardrail_check_chain.ainvoke(
        {"question": state["messages"][-1] if state["messages"] else ""}, config=config
    )

    # 2. 根据决策行动
    if guard_result.decision == "continue":
        log.info("-----Pass guardrails check-----")
        ask_messages = apply_prompt_template("get_additional", state)
        response = await get_chat_model().ainvoke(ask_messages, config=config)
        return Command(
            goto="__end__",
            update={"messages": [response]}
        )
    else:
        log.info("-----Fail to pass guardrails check-----")
        return Command(
            goto="__end__",
            update={"messages": [AIMessage(content="抱歉，我家暂时没有这方面的商品，可以在别家看看哦~")]}
        )


async def create_research_plan(
        state: OverallState, *, config: RunnableConfig
) -> Command[Literal["check_hallucinations", "__end__"]]:
    """通过查询本地知识库回答客户问题，执行任务分解，创建分布查询计划。

    Args:
        state (AgentState): 当前代理状态，包括对话历史。
        config (RunnableConfig): 用于配置计划生成的模型。
    """
    thread_id = config.get("configurable", {}).get("thread_id", None)
    log = logger.bind(thread_id=thread_id)

    chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
    latest_input = state["messages"][-1].content

    contextualize_question_chain = get_contextualize_question_chain()

    log.info(f"Original Input: {latest_input}")

    # 只有当有历史记录时才需要重写，否则直接使用原问题
    if chat_history:
        reformulated_msg = await contextualize_question_chain.ainvoke(
            {"chat_history": chat_history, "input": latest_input},
            config=config
        )
        final_query = reformulated_msg.content
        log.info(f"Reformulated Query: {final_query}")
    else:
        final_query = latest_input

    question_payload = {"question": final_query}

    # 第一步：安全护栏检查(GuardrailCheck)
    guardrail_check_chain = get_guardrail_check_chain()
    guard_result: GuardrailsOutput = await guardrail_check_chain.ainvoke(question_payload, config=config)

    # 2. 根据决策行动
    if guard_result.decision == "continue":
        log.info("-----Pass guardrails check-----")
        graph_rag_agent = build_graph_rag_agent()
        response = await graph_rag_agent.ainvoke(question_payload, config=config)

        return Command(
            goto="check_hallucinations",
            update={
                "messages": [AIMessage(content=response["summary"])],
                "documents": response["context"],
            }
        )
    else:
        log.info("-----Fail to pass guardrails check-----")
        return Command(
            goto="__end__",
            update={"messages": [AIMessage(content="抱歉，我家暂时没有这方面的商品，可以在别家看看哦~")]}
        )


async def check_hallucinations(
        state: OverallState, *, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    """Analyze the user's query and checks if the response is supported by the set of facts based on the document retrieved,
    providing a binary score result.

    This function uses a language model to analyze the user's query and gives a binary score result.

    Args:
        state (AgentState): The current state of the agent, including conversation history.
        config (RunnableConfig): Configuration with the model used for query analysis.

    Returns:
        dict[str, Router]: A dictionary containing the 'router' key with the classification result (classification type and logic).
    """
    thread_id = config.get("configurable", {}).get("thread_id", None)
    log = logger.bind(thread_id=thread_id)

    log.info("---CHECK HALLUCINATIONS---")

    system_prompt = CHECK_HALLUCINATIONS.format(
        documents=state["documents"],
        generation=state["messages"][-1]
    )
    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    response: GradeHallucinations = cast(
        GradeHallucinations, await get_router_model().
        with_structured_output(GradeHallucinations).
        ainvoke(messages, config=config)
    )

    return Command(
        goto="__end__",
        update={
            "hallucination": response,
        }
    )


async def create_image_query(
        state: OverallState, *, config: RunnableConfig
) -> Dict[str, List[BaseMessage]]:
    # TODO
    pass


async def create_file_query(
        state: OverallState, *, config: RunnableConfig
) -> Dict[str, List[BaseMessage]]:
    """Create a file query."""
    pass
    # TODO
