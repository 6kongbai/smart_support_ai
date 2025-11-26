from typing import Literal

from app.graph.state import OverallState


def route_conditional_edge(
        state: OverallState
) -> Literal[
    "respond_to_general_query", "get_additional_info", "create_research_plan", "create_image_query", "create_file_query"]:
    """根据 state.jump_to 的分类结果映射到下一跳节点。"""
    match state["next"]:
        case "general-query":
            return "respond_to_general_query"
        case "additional-query":
            return "get_additional_info"
        case "graphrag-query":
            return "create_research_plan"
        case "image-query":
            return "create_image_query"
        case "file-query":
            return "create_file_query"
        case _:
            raise ValueError(f"Invalid jump_to: {state["next"]}")
