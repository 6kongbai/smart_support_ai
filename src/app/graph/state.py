from typing import NotRequired, Annotated, TypedDict, List

from langchain_core.messages import AnyMessage
from langgraph.channels import EphemeralValue, LastValue
from langgraph.graph import add_messages

from app.graph.types import GradeHallucinations, JumpTo


class InputState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]


class OutputState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]


class OverallState(TypedDict):
    next: NotRequired[Annotated[JumpTo, EphemeralValue]]
    hallucination: NotRequired[Annotated[GradeHallucinations, EphemeralValue]]
    reasoning: NotRequired[Annotated[str | None, EphemeralValue]]
    messages: Annotated[List[AnyMessage], add_messages]
    documents: NotRequired[Annotated[str, EphemeralValue]]
    reformulate: Annotated[bool | None, LastValue]
    original_question: Annotated[str | None, LastValue]
    question: Annotated[str | None, LastValue]
