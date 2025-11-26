from langgraph.graph import StateGraph

from app.graph.edges import route_conditional_edge
from app.graph.nodes import analyze_and_route_query, get_additional_info, respond_to_general_query, \
    create_research_plan, create_image_query, create_file_query, check_hallucinations
from app.graph.state import OverallState, InputState, OutputState


def _build_base_graph():
    builder = StateGraph(
        OverallState,
        input_schema=InputState,
        output_schema=OutputState
    )

    builder.add_node(analyze_and_route_query)
    builder.add_node(respond_to_general_query)
    builder.add_node(get_additional_info)
    builder.add_node("create_research_plan", create_research_plan)  # 这里是子图
    builder.add_node(create_image_query)
    builder.add_node(create_file_query)
    builder.add_node(check_hallucinations)

    builder.set_entry_point("analyze_and_route_query")

    builder.add_conditional_edges(
        "analyze_and_route_query",
        route_conditional_edge,
        ["respond_to_general_query", "get_additional_info", "create_research_plan", "create_image_query",
         "create_file_query"])

    return builder


def build_agent():
    """Build and return the agent workflow graph without memory."""
    # build state graph
    builder = _build_base_graph()
    return builder.compile()


if __name__ == '__main__':
    graph = build_agent()
    print(graph.get_graph().draw_mermaid())
