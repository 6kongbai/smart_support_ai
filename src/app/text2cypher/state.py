import operator
from typing import TypedDict, Optional, List, Annotated


class InputState(TypedDict):
    question: str
    llm_validation: bool


class OverallState(TypedDict):
    question: str
    cypher: str
    errors: Annotated[List[str], operator.add]
    llm_validation: bool


# 3. 输出状态：workflow.invoke() 最终返回的数据
class OutputState(TypedDict):
    cypher: str
