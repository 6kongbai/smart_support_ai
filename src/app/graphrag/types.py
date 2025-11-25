from typing import List, TypedDict, Literal, Dict, Any, Union, Optional, Annotated

from pydantic import BaseModel, Field


class Parameter(BaseModel):
    """参数定义"""
    name: str = Field(..., description="参数名称")
    value: Union[str, int, float] = Field(..., description="参数值")


class TemplateDecision(BaseModel):
    """预定义查询的决策结果"""
    template_id: str = Field(..., description="从注册表中选择的最匹配的模版ID")
    parameters: List[Parameter] = Field(
        ...,
        description="提取的查询参数。",
    )
    reasoning: str = Field(..., description="选择该模版的理由")


class TaskResult(TypedDict):
    # 任务ID
    id: str
    # 任务问题
    question: str
    # 任务结果
    answer: str
    # 使用的工具
    tool: str
    # 状态
    status: Literal["completed", "failed"]


class Task(BaseModel):
    """单个子任务的定义：包含具体问题和对应的处理工具"""

    sub_query: str = Field(
        ...,
        description="拆解后、去指代、独立完整的子查询语句。"
    )

    selected_tool: Literal["text2cypher", "predefined_cypher", "web_search"] = Field(
        ...,
        description="根据预设规则为该子任务选择的最优工具。"
    )


class PlannerOutput(BaseModel):
    """
    任务规划器的输出。
    包含一系列有序的子任务，每个子任务都绑定了特定的工具。
    """

    # 增加一个思考字段，让模型在生成列表前先通过 CoT 提升准确率
    reasoning: str = Field(
        ...,
        description="简要分析用户的意图，解释为什么需要这样拆解以及为什么选择这些工具。"
    )

    tasks: List[Task] = Field(
        ...,
        description="分解并路由后的任务列表。"
    )


class WebSearchInput(BaseModel):
    search_query: str = Field(
        ...,
        description="需要进行搜索的内容, 建议搜索 query 不超过 70 个字符"
    )
    count: Optional[int] = Field(
        10,
        ge=1,
        le=50,
        description="返回结果的条数，可填范围：1-50，默认为10。"
    )
    search_domain_filter: Optional[str] = Field(
        None,
        description="用于限定搜索结果的范围，仅返回指定白名单域名的内容，如: www.example.com。"
    )
    search_recency_filter: Optional[Literal[
        "oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"
    ]] = Field(
        "noLimit",
        description=(
            "搜索指定时间范围内的网页。默认为 noLimit "
            "可填值：oneDay/oneWeek/oneMonth/oneYear/noLimit"
        )
    )
    content_size: Optional[Literal["medium", "high"]] = Field(
        "medium",
        description=(
            "控制网页摘要的字数；默认 medium（400-600字）"
            "high（约2500字，成本更高）"
        )
    )


class ResponseFormat(BaseModel):
    """Response schema for the agent."""
    response: Annotated[str, Field(description="联网查询的结果的总结")]
