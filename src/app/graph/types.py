from typing import Literal, Annotated

from pydantic import BaseModel, Field


class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""
    binary_score: Literal["yes", "no"] = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
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
    reasoning: Annotated[str, Field(
        description="简要的分析用户的意图，然后给出选择这个路由的原因"
    )]
    next: Annotated[JumpTo, Field(
        description="根据上述分析，选择最匹配的路由目标。"
    )]
    confidence: Annotated[int, Field(
        description="对该分类判断的置信度评分，范围 1 到 5（5表示非常确定，1表示完全不确定）。"
    )]
