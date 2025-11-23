from typing import List

from langgraph.types import Send

from app.graphrag.state import OverallState, TaskState


def map_tasks_to_tool_selection(state: OverallState) -> List[Send]:
    tasks = state.get("plans", [])

    sends = []
    for i, q in enumerate(tasks):
        # 构造发给 Router 的初始状态
        sub_state = TaskState(
            id=f"t_{i}",
            question=q,
            target_tool="None",
        )
        sends.append(Send("tool_selection", sub_state))
    return sends
