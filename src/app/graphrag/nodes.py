import json
from typing import Literal, cast, Any, List, Dict, Union

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from loguru import logger

from app.db.neo4j.client import get_async_session
from app.graphrag.state import OverallState, TaskState
from app.graphrag.tools import CYPHER_TEMPLATES
from app.graphrag.types import PlannerOutput, TemplateDecision, Parameter
from app.graphrag.utils import get_planner_chain, get_summarize_chain, create_result_command, \
    get_predefined_cypher_chain
from app.text2cypher.builder import build_text2pycher_agent
from app.text2cypher.state import OutputState as CypherOutput


async def planner(
        state: OverallState, *, config: RunnableConfig
) -> dict[str, Any]:
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

    logger.info(f"Planner Reasoning: {planner_output.reasoning}")
    logger.info(f"Total Sub Tasks: {len(planner_output.tasks)}")

    return {"planned_tasks": planner_output.tasks}


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
    task_id = state["id"]
    question = state["question"]

    logger.info(f"[{task_id}] Start Predefined Query: {question}")

    try:
        chain = get_predefined_cypher_chain()

        # --- Step 1: LLM 模版选择与参数提取 ---
        decision: TemplateDecision = await chain.ainvoke({"question": question}, config=config)

        parameters_list: List[Parameter] = decision.parameters
        if decision.template_id == "NONE" or decision.template_id not in CYPHER_TEMPLATES:
            raise ValueError(f"无法匹配到预定义模版，意图识别结果: {decision.template_id}")

        # 获取模版详情
        template_obj = CYPHER_TEMPLATES[decision.template_id]
        required_params: List[str] = template_obj.required_params

        # --- Step 2 : 参数强校验 ---
        parameters: Dict[str, Union[str, int, float]] = {
            p.name: p.value
            for p in parameters_list
        }

        missing_params = [
            required_param
            for required_param in required_params
            if required_param not in parameters
        ]

        if missing_params:
            raise ValueError(
                f"模版 '{decision.template_id}' 缺少必要参数: {missing_params}. "
                "请检查用户问题中是否提供了相应实体。"
            )

        logger.info(f"[{task_id}] Selected Template: {decision.template_id} | Params: {parameters}")

        # --- Step 3: 执行数据库查询 ---
        executed_cypher = template_obj.cypher
        logger.info(f"[{task_id}] Executing Cypher: {executed_cypher} with {parameters}")
        async with get_async_session() as session:
            # 使用提取的参数运行查询
            result_cursor = await session.run(executed_cypher, parameters)
            raw_data = await result_cursor.data()

            if not raw_data:
                result_str = "查询执行成功，但未返回任何结果。"
            else:
                result_str = json.dumps(raw_data, ensure_ascii=False, default=str)

    except ValueError as ve:
        error_msg = f"校验失败: {str(ve)}"
        logger.warning(f"[{task_id}] Validation Warning: {error_msg}")
        return create_result_command(state, error_msg, status="failed")

    except Exception as e:
        error_msg = f"数据库/异步执行失败: {type(e).__name__} - {str(e)}"
        logger.error(f"[{task_id}] Execution Error: {error_msg}")
        return create_result_command(state, error_msg, status="failed")

    # --- Step 4: 返回成功结果 ---
    return create_result_command(state, result_str, status="completed")


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
