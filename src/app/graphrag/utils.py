import asyncio
from functools import cache
from typing import Literal

from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSerializable
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from pydantic import BaseModel

from app.graphrag.prompts import create_planner_prompt_template, create_summarization_prompt_template, \
    create_predefined_cypher_prompt_template, get_web_search_prompt
from app.graphrag.state import TaskState
from app.graphrag.tools import mcp_client
from app.graphrag.types import PlannerOutput, TaskResult, TemplateDecision, ResponseFormat
from app.llms.llm import get_router_model, get_chat_model
from app.text2cypher.builder import build_text2cypher_agent


@cache
def get_planner_chain() -> RunnableSerializable[dict, BaseModel]:
    llm = get_router_model()
    prompt = create_planner_prompt_template()
    return prompt | llm.with_structured_output(PlannerOutput)


@cache
def get_summarize_chain() -> RunnableSerializable[dict, str]:
    llm = get_chat_model()
    prompt = create_summarization_prompt_template()
    return prompt | llm | StrOutputParser()


@cache
def get_predefined_cypher_chain():
    llm = get_router_model()
    prompt = create_predefined_cypher_prompt_template()
    return prompt | llm.with_structured_output(TemplateDecision)


@cache
def get_text2cypher_agent():
    return build_text2cypher_agent()


_web_search_agent: CompiledStateGraph = None
_web_search_agent_lock = asyncio.Lock()


async def get_web_search_agent() -> CompiledStateGraph:
    global _web_search_agent

    # 快路径：已经初始化过了就直接返回
    if _web_search_agent is not None:
        return _web_search_agent

    # 慢路径：第一次初始化需要加锁，防止并发重复创建
    async with _web_search_agent_lock:
        # 双重检查：避免排队等待锁的协程重复初始化
        if _web_search_agent is None:
            tools = await mcp_client.get_tools()
            _web_search_agent = create_agent(
                model=get_chat_model(),
                tools=tools,
                system_prompt=get_web_search_prompt(),
                response_format=ResponseFormat,
            )

    return _web_search_agent


def create_result_command(
        state: TaskState,
        answer: str,
        status: Literal["completed", "failed"],
        tool: str = ""
) -> Command[Literal["summarize"]]:
    """
    辅助函数：统一构建返回的 Command 对象，减少代码重复。
    """
    return Command(
        goto="summarize",
        update={
            "results": [TaskResult(
                id=state["id"],
                question=state["question"],
                answer=answer,
                tool=tool if tool else state["target_tool"],
                status=status
            )]
        }
    )
