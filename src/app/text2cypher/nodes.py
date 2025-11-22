import asyncio
from typing import Literal, List

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from loguru import logger
from neo4j.exceptions import CypherSyntaxError, ClientError

from app.db.neo4j.client import get_async_session
from app.db.neo4j.utils import get_corrector
from app.text2cypher.state import InputState, OverallState
from app.text2cypher.types import ValidateCypherOutput
from app.text2cypher.utils import get_cypher_generation_chain, WRITE_CLAUSES_REGEX, get_validate_cypher_chain, \
    check_value_exists_async, should_validate_property, get_correct_cypher_chain


async def generation_cypher(
        state: InputState, *, config: RunnableConfig
) -> Command[Literal["validate_cypher"]]:
    cypher_generation_chain = get_cypher_generation_chain()

    cypher = await cypher_generation_chain.ainvoke(state["question"], config=config)
    logger.info(f"生成的Cypher查询语句为: {cypher}")

    return Command(
        goto="validate_cypher",
        update={
            "cypher": cypher,
        }
    )


async def validate_cypher(
        state: OverallState, *, config: RunnableConfig
) -> Command[Literal["validate_cypher_with_llm", "validate_cypher_with_schema"]]:
    original_cypher = state["cypher"]
    errors = list()

    # --- Step 1: 自动修正 (Auto-Correction) ---
    corrector = get_corrector()
    cypher = corrector(original_cypher)
    if cypher != original_cypher:
        logger.error(f"Cypher Query Corrected: {original_cypher} -> {cypher}")

    # --- Step 2: 安全检查 (Security Check) ---
    if match := WRITE_CLAUSES_REGEX.search(cypher):
        errors.append(f"Security Alert: Cypher contains restricted write clause '{match.group(1).upper()}'")
        logger.error(errors[-1])

    # --- Step 3: 语法检查 (Syntax Check via EXPLAIN) ---
    try:
        async with get_async_session() as session:
            result = await session.run(f"EXPLAIN {cypher}")
            await result.consume()

    except (CypherSyntaxError, ClientError) as e:
        errors.append(f"Syntax Error: {e.message}")
        logger.error(errors[-1])
    except Exception as e:
        errors.append(f"Execution Error: {str(e)}")
        logger.error(errors[-1])

    # --- Step 4: 路由决策 (Routing) ---
    update_payload = {
        "errors": errors,
        "cypher": cypher,
    }

    if state.get("llm_validation", False):
        return Command(
            goto="validate_cypher_with_llm",
            update=update_payload
        )
    else:
        return Command(
            goto="validate_cypher_with_schema",
            update=update_payload
        )


async def validate_cypher_with_llm(
        state: OverallState, *, config: RunnableConfig
) -> Command[Literal["correction_cypher", "__end__"]]:
    errors: List[str] = []
    mapping_errors: List[str] = []

    validate_cypher_chain = get_validate_cypher_chain()
    llm_output: ValidateCypherOutput = await validate_cypher_chain.ainvoke(
        {
            "question": state["question"],
            "cypher": state["cypher"],
        }
    )
    if llm_output.errors:
        errors.extend(llm_output.errors)
        logger.error(f"LLM Validation Errors: {llm_output.errors}")

    target_filters = [
        f for f in llm_output.filters
        if should_validate_property(f.node_label, f.property_key)
    ]
    if target_filters:
        validation_tasks = [check_value_exists_async(f) for f in target_filters]

        if validation_tasks:
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, str):
                    mapping_errors.append(res)
                elif isinstance(res, Exception):
                    errors.append(f"DB Async Check Error: {str(res)}")

    if mapping_errors:  # 场景 A: 数据映射错误 (Mapping Errors)，用户的意图是：如果查不到值，就结束并告诉用户。
        logger.error(f"数据映射错误: {mapping_errors}")
        final_errors = errors + mapping_errors
        return Command(
            goto="__end__",
            update={
                "errors": final_errors,  # 将所有错误传递给最终回复生成器
            }
        )

    elif errors:  # 场景 B: 语法/Schema 错误 (Syntax Errors)
        logger.error(f"语法/Schema 错误: {errors}")
        return Command(
            goto="correction_cypher",
            update={
                "errors": errors,
            }
        )

    else:  # 场景 C: 无错误 (Success)
        logger.info("无错误")
        return Command(
            goto="__end__",  # 应该跳转到执行 Cypher 的节点，或者结束
        )


async def validate_cypher_with_schema(
        state: OverallState, *, config: RunnableConfig
):
    pass


async def correction_cypher(
        state: OverallState, *, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    correct_cypher_chain = get_correct_cypher_chain()
    corrected_cypher_update = await correct_cypher_chain.ainvoke(
        {
            "question": state.get("question"),
            "errors": state.get("errors"),
            "cypher": state.get("cypher"),
        }
    )
    return Command(
        goto="__end__",
        update={
            "cypher": corrected_cypher_update,
        }
    )
