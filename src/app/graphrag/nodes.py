import json
from typing import Literal, cast, List, Any, Coroutine

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command, Send
from loguru import logger
from pydantic import BaseModel

from app.db.neo4j.client import get_async_session
from app.graphrag.state import OverallState, TaskState
from app.graphrag.types import PlannerOutput, TaskResult
from app.graphrag.utils import get_planner_chain, get_summarize_chain, create_result_command, get_tool_selection_chain
from app.text2cypher.builder import build_text2pycher_agent
from app.text2cypher.state import OutputState as CypherOutput


async def planner(
        state: OverallState, *, config: RunnableConfig
) -> dict[str, list[str]]:
    """
    Break user query into chunks, if appropriate.
    """

    planner_chain = get_planner_chain()
    planner_output = cast(
        PlannerOutput, await planner_chain.ainvoke(
            {"question": state["question"]},
            config=config
        )
    )

    # 日志打印格式，分别打印每个任务
    logger.info(f"Total Sub Task: {len(planner_output.plans)}")

    for i, plan in enumerate(planner_output.plans):
        logger.info(f"Sub Task[{i + 1}]: {plan}")

    return {"plans": planner_output.plans}


async def tool_selection(
        state: TaskState, *, config: RunnableConfig
) -> Command[Literal["text2cypher_query", "predefined_cypher_query", "network_query", "customer_query", "summarize"]]:
    tool_selection_chain = get_tool_selection_chain()
    tool_selection_output: BaseModel = await tool_selection_chain.ainvoke(
        {"question": state.get("question", "")}
    )

    if tool_selection_output is None:
        return create_result_command(state, "生成查询语句失败", status="failed")

    tool_name: str = tool_selection_output.model_json_schema().get("title", "")

    return Command(
                goto=Send(
                    tool_name,
                    TaskState(
                        id=state["id"],
                        question=state["question"],
                        target_tool=tool_name,
                    )
                )
            )


async def text2cypher_query(
        state: TaskState, *, config: RunnableConfig
) -> Command[Literal["summarize"]]:
    # Step 1. 生成 Cypher 语句
    try:
        generate_cypher_agent = build_text2pycher_agent()
        inputs = {
            "question": state["question"],
            "llm_validation": True
        }

        response: CypherOutput = await generate_cypher_agent.invoke(inputs, config)

        if response["status"] == "failed":
            return create_result_command(state, "生成查询语句失败", status="failed")
        elif response["status"] == "data_no_exist":
            return create_result_command(state, "根据现有知识库无法查到相关数据", status="failed")

        cypher_query_str = response["cypher"]
        logger.info(f"生成的 Cypher: {cypher_query_str}")

    except Exception as e:
        logger.exception(f"Cypher 生成阶段出错: {e}")
        return create_result_command(state, f"生成语句时发生系统错误: {str(e)}", status="failed")

    # Step 2. 运行 Cypher 并转存为 String
    async with get_async_session() as session:
        try:
            result_cursor = await session.run(cypher_query_str)
            # 1. 提取数据到内存 (List[Dict])
            raw_data = await result_cursor.data()
            # 2. 判断数据是否为空
            if not raw_data:
                answer_content = "查询执行成功，但未返回任何结果。"
            else:
                # 3. 序列化为 JSON 字符串
                answer_content = json.dumps(raw_data, ensure_ascii=False, default=str)
            # Case 4: 数据库查询正常结束 (无论有无数据)
            return create_result_command(state, answer_content, status="completed")

        except Exception as e:
            logger.exception(f"数据库执行出错: {e}")
            return create_result_command(state, f"数据库查询执行出错: {str(e)}", status="failed")


async def predefined_cypher_query(
        state: TaskState, *, config: RunnableConfig
) -> Command[Literal["summarize"]]:
    pass


async def network_query(
        state: TaskState, *, config: RunnableConfig
) -> Command[Literal["summarize"]]:
    pass


async def customer_query(
        state: TaskState, *, config: RunnableConfig
) -> Command[Literal["summarize"]]:
    pass


async def summarize(
        state: OverallState, *, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    results = state.get("results", [])
    context = "\n".join([f"- {r["tool"]}: {r["answer"]}" for r in results])
    if context:
        summarize_chain = get_summarize_chain()
        summary = await summarize_chain.ainvoke(
            {
                "question": state["question"],
                "context": context
            },
            config=config
        )
    else:
        summary = ""
    return Command(
        goto="__end__",
        update={"summary": summary}
    )
