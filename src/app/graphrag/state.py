import operator
from typing import Annotated, List

from typing_extensions import TypedDict

from app.graphrag.types import TaskResult, Task


class InputState(TypedDict):
    """The input state for multi-agent workflows."""
    question: str


class OverallState(TypedDict):
    """The main state in multi-agent workflows."""

    question: str
    results: Annotated[List[TaskResult], operator.add]
    tasks: List[Task]
    summary: str
    answer: str


class OutputState(TypedDict):
    """The final output for multi-agent workflows."""
    answer: str


class TaskState(TypedDict):
    """
    表示一个从复杂用户查询中分解出的独立子任务。
    它是 Agent 在 Knowledge Graph (知识图谱) 中执行操作的基本单元。
    """
    id: str
    question: str
    target_tool: str
