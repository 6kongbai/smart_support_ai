from operator import add
from typing import Annotated, List

from typing_extensions import TypedDict

from app.graphrag.types import Task


class InputState(TypedDict):
    """The input state for multi-agent workflows."""
    question: str


class OverallState(TypedDict):
    """The main state in multi-agent workflows."""

    question: str
    tasks: Annotated[List[Task], add]
    next: str
    answer: str


class OutputState(TypedDict):
    """The final output for multi-agent workflows."""
    answer: str
