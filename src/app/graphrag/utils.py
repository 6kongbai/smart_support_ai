from typing import Literal

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSerializable
from langgraph.types import Command
from pydantic import BaseModel

from app.graphrag.prompts import create_planner_prompt_template, create_summarization_prompt_template, \
    create_predefined_cypher_prompt_template
from app.graphrag.state import TaskState
from app.graphrag.types import PlannerOutput, TaskResult, TemplateDecision
from app.llms.llm import get_router_model, get_chat_model

TOOL_NODE_MAPPING = {
    "text2cypher": "text2cypher_query",  # LLM输出名 : Graph节点名
    "predefined_cypher": "predefined_cypher_query",
    "web_search": "network_query"
}


def get_planner_chain() -> RunnableSerializable[dict, BaseModel]:
    llm = get_router_model()
    prompt = create_planner_prompt_template()
    return prompt | llm.with_structured_output(PlannerOutput)


def get_summarize_chain() -> RunnableSerializable[dict, str]:
    llm = get_chat_model()
    prompt = create_summarization_prompt_template()
    return prompt | llm | StrOutputParser()


def get_predefined_cypher_chain():
    llm = get_router_model()
    prompt = create_predefined_cypher_prompt_template()
    return prompt | llm.with_structured_output(TemplateDecision)

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
