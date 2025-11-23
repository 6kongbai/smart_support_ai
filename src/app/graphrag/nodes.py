import json
from typing import Literal, cast

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from loguru import logger

from app.db.neo4j.client import get_async_session
from app.graphrag.state import InputState, OverallState, TaskState
from app.graphrag.types import PlannerOutput
from app.graphrag.utils import get_planner_chain, get_summarize_chain
from app.text2cypher.builder import build_text2pycher_agent


async def planner(
        state: InputState, *, config: RunnableConfig
) -> Command[Literal["cypher_query"]]:
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
    logger.info(f"Total Sub Task: {len(planner_output.tasks)}")

    for i, task in enumerate(planner_output.tasks):
        logger.info(f"Sub Task[{i + 1}]: {task.question}")

    return Command(
        goto="cypher_query",
        update={"tasks": planner_output.tasks},
    )


async def cypher_query(
        state: TaskState, *, config: RunnableConfig
):
    task = state["task"]
    task.status = "in_progress"

    # Step 1. 生成 Cypher 语句
    try:
        generate_cypher_agent = build_text2pycher_agent()
        inputs = {
            "question": task.question,
            "llm_validation": True
        }

        response = await generate_cypher_agent.invoke(inputs, config)

        if response.status == "failed":
            task.status = "failed"
            task.record = "生成查询语句失败"
            return Command(goto="summarize")
        elif response.status == "data_no_exist":
            task.status = "failed"
            task.record = "根据现有知识库无法查到相关数据"
            return Command(goto="summarize")

        cypher_query_str = response.cypher
        logger.info(f"生成的 Cypher: {cypher_query_str}")

    except Exception as e:
        logger.error(f"Cypher 生成阶段出错: {e}", exc_info=True)
        task.status = "failed"
        task.record = f"生成语句时发生系统错误: {str(e)}"
        return Command(goto="summarize")

    # Step 2. 运行 Cypher 并转存为 String
    async with get_async_session() as session:
        try:
            result_cursor = await session.run(cypher_query_str)

            # 1. 提取数据到内存 (List[Dict])
            raw_data = await result_cursor.data()

            # 2. 判断数据是否为空
            if not raw_data:
                # 即使没报错，查不到数据也需要给一个明确的字符串描述
                task.record = "查询执行成功，但未返回任何结果。"
                # 状态可以根据业务定，有时没查到也是一种 completed
                task.status = "completed"
            else:
                # 3. 序列化为 JSON 字符串
                task.record = json.dumps(raw_data, ensure_ascii=False, default=str)
                task.status = "completed"

            logger.info(f"Cypher 执行成功")

        except Exception as e:
            # 捕获所有数据库运行时错误（语法错误、连接超时等）
            logger.error(f"数据库执行出错: {e}", exc_info=True)
            task.status = "failed"
            task.record = f"数据库查询执行出错: {str(e)}"

    return Command(goto="summarize")


async def summarize(
        state: OverallState, *, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    context = "\n".join([task.record for task in state["tasks"]])
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
