import operator
from typing import List

from typing_extensions import Annotated, TypedDict, Literal


class InputState(TypedDict):
    question: str
    llm_validation: bool


class OverallState(TypedDict):
    question: str
    cypher: str
    errors: Annotated[List[str], operator.add]
    status: Literal["success", "failed", "data_no_exist"]
    llm_validation: bool


class OutputState(TypedDict):
    cypher: str
    status: Literal["success", "failed", "data_no_exist"]
