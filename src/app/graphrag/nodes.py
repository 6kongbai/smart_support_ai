from typing import Any, Dict, cast

from langchain_core.messages import SystemMessage, HumanMessage

from loguru import logger
from app.db.neo4j.utils import get_graph_schema
from app.graphrag.state import InputState
from app.graphrag.types import PlannerOutput
from app.llms.llm import get_chat_model, get_router_model
from app.prompts.template import get_prompt_template


async def planner(state: InputState) -> Dict[str, Any]:
    """
    Break user query into chunks, if appropriate.
    """

    planner_prompt = get_prompt_template(
        "graphrag/planner",
        graph_context=get_graph_schema()
    )

    messages = [SystemMessage(content=planner_prompt)] + [HumanMessage(content=state["question"])]

    planner_output = cast(
        PlannerOutput, await get_router_model()
        .with_structured_output(PlannerOutput)
        .ainvoke(messages)
    )

    # 日志打印格式，分别打印每个任务
    logger.info(f"Total Sub Task: {len(planner_output.tasks)}")

    for i, task in enumerate(planner_output.tasks):
        logger.info(f"Sub Task[{i + 1}]: {task.question}")

    return {
        "next": 'tool_selection',
        "tasks": planner_output.tasks
    }



