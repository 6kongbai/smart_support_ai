from typing import List

from langgraph.types import Send
from loguru import logger

from app.graphrag.state import OverallState, TaskState

TOOL_NODE_MAPPING = {
    "text2cypher": "text2cypher_query",  # LLM输出名 : Graph节点名
    "predefined_cypher": "predefined_cypher_query",
    "web_search": "network_query"
}

def distribute_tasks(state: OverallState) -> List[Send]:
    tasks = state.get("tasks", [])

    sends = []
    for i, task in enumerate(tasks):
        node_name = TOOL_NODE_MAPPING.get(task.selected_tool)

        if not node_name:
            logger.error(f"Unknown tool selected: {task.selected_tool}, skipping.")
            continue

        # 2. 构造分发对象
        sends.append(Send(
            node=node_name,
            arg=TaskState(
                id=f"t_{i}",
                question=task.sub_query,
                target_tool=task.selected_tool
            )
        ))
    return sends
