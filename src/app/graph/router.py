from app.graph.types import State


def route_query(state: State) -> str:
    """根据 state.jump_to 的分类结果映射到下一跳节点。"""

    match state["jump_to"]:
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
            raise ValueError(f"Invalid jump_to: {state["jump_to"]}")
