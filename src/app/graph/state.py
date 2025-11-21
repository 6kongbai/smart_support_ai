from typing import NotRequired, Annotated

from langgraph.channels import EphemeralValue
from langgraph.graph import MessagesState

from app.graph.types import GradeHallucinations, JumpTo


class InputState(MessagesState):
    pass


class OutputState(MessagesState):
    answer: str


class OverallStates(InputState, OutputState):
    jump_to: NotRequired[Annotated[JumpTo | None, EphemeralValue]]
    hallucination: NotRequired[Annotated[GradeHallucinations, EphemeralValue]]
    reasoning: NotRequired[Annotated[str | None, EphemeralValue]]
