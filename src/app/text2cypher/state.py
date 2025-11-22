import operator
from typing import List

from typing_extensions import Annotated, TypedDict


class InputState(TypedDict):
    question: str
    llm_validation: bool


class OverallState(TypedDict):
    question: str
    cypher: str
    errors: Annotated[List[str], operator.add]
    llm_validation: bool


class OutputState(TypedDict):
    cypher: str
