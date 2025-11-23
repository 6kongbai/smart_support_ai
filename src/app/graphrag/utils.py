from typing import Literal

from langchain_core.output_parsers import StrOutputParser, PydanticToolsParser
from langchain_core.runnables import RunnableSerializable
from langgraph.types import Command
from pydantic import BaseModel

from app.graphrag.prompts import create_planner_prompt_template, create_summarization_prompt_template, \
    create_tool_selection_prompt_template
from app.graphrag.state import TaskState
from app.graphrag.tools import tools
from app.graphrag.types import PlannerOutput, TaskResult
from app.llms.llm import get_router_model, get_chat_model, get_function_call_model


def get_planner_chain() -> RunnableSerializable[dict, BaseModel]:
    llm = get_router_model()
    prompt = create_planner_prompt_template()
    return prompt | llm.with_structured_output(PlannerOutput)


def get_summarize_chain() -> RunnableSerializable[dict, str]:
    llm = get_chat_model()
    prompt = create_summarization_prompt_template()
    return prompt | llm | StrOutputParser()


def get_tool_selection_chain() -> RunnableSerializable[dict, BaseModel]:
    llm = get_function_call_model()
    prompt = create_tool_selection_prompt_template()
    return prompt | llm.bind_tools(tools, tool_choice="any", parallel_tool_calls=False) | PydanticToolsParser(
        tools=tools, first_tool_only=True)


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
