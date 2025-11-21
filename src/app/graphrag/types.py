from operator import add
from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class CypherOutputState(TypedDict):
    task: Annotated[list, add]
    statement: str
    parameters: Optional[Dict[str, Any]]
    errors: List[str]
    records: List[Dict[str, Any]]
    steps: List[str]


class Task(BaseModel):
    """
    表示一个从复杂用户查询中分解出的独立子任务。
    它是 Agent 在 Knowledge Graph (知识图谱) 中执行操作的基本单元。
    """
    question: Annotated[
        str,
        Field(
            description="该子任务需要回答的具体问题或执行的操作，必须是完整的句子。"
        )
    ]

    parent_task: Annotated[
        str,
        Field(
            description="派生出该子任务的原始用户查询或父任务的完整文本。"
        )
    ]

    status: Annotated[
        Literal["pending", "in_progress", "completed", "failed"],
        Field(
            default="pending",
            description="任务的当前执行状态。'pending' (待处理), 'in_progress' (处理中), 'completed' (已完成), 'failed' (失败)."
        )
    ]

    data: Annotated[
        Optional[CypherOutputState],
        Field(
            default=None,
            description="用于承载该任务在执行过程中产生的中间数据或 Cypher 查询结果。"
        )
    ]


class PlannerOutput(BaseModel):
    """
    由任务规划组件 (Planner Agent) 生成的结构化输出。
    它包含了一组用于解决原始用户查询的独立且不重复的子任务列表。
    """

    tasks: List[Task] = Field(
        default=[],
        description="解决用户原始查询所需完成的独立且不重复的子任务列表。如果原始问题很简单，该列表将只包含一个任务（即原问题）。"
    )
