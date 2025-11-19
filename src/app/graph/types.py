from typing import NotRequired, Literal, Annotated

from langgraph.channels import EphemeralValue
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""
    binary_score: str = Field(
        default="0",
        description="Answer is grounded in the facts, '1' or '0'"
    )


class GuardrailsOutput(BaseModel):
    """
    格式化输出，用于判断用户的问题是否与图谱内容相关
    """
    reasoning: str = Field(
        description="简短的思考过程，解释为什么做出这个判断。例如：'用户询问的是冰箱，属于智能家居范围' 或 '用户询问天气，属于外部信息'。"
    )
    decision: Literal["continue", "end"] = Field(
        description="最终决策：continue 表示进入业务流程，end 表示与经营内容无关。"
    )


JumpTo = Literal["general-query", "additional-query", "graphrag-query", "image-query", "file-query"]


class Router(BaseModel):
    """Determine user intent and the next routing step."""

    cause: Annotated[str, Field(description="简短分析用户的意图，以及判断是否缺少关键参数的依据。")]
    next: Annotated[JumpTo, Field(..., description="下一步的路由目标")]


class State(MessagesState):
    jump_to: NotRequired[Annotated[JumpTo | None, EphemeralValue]]
    hallucination: NotRequired[Annotated[GradeHallucinations, EphemeralValue]]
    cause: NotRequired[Annotated[str | None, EphemeralValue]]
    answer: NotRequired[str]
