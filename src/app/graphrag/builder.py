from langgraph.graph import StateGraph

from app.graphrag.edges import distribute_tasks
from app.graphrag.nodes import planner, text2cypher_query, predefined_cypher_query, network_query, summarize
from app.graphrag.state import OverallState, InputState, OutputState


def _build_base_graph():
    builder = StateGraph(
        OverallState,
        input_schema=InputState,
        output_schema=OutputState
    )

    builder.add_node(planner)
    builder.add_node(text2cypher_query)
    builder.add_node(predefined_cypher_query)
    builder.add_node(network_query)
    builder.add_node(summarize)

    builder.set_entry_point("planner")

    # 添加条件边：从 planner 出来后，执行 distribute_tasks
    builder.add_conditional_edges(
        "planner",
        distribute_tasks,
        ["text2cypher_query", "predefined_cypher_query", "network_query"]  # 允许的目标节点
    )

    return builder


def build_graph_rag_agent():
    """Build and return the agent workflow graph without memory."""
    # build state graph
    builder = _build_base_graph()
    return builder.compile()


if __name__ == '__main__':
    graph = build_graph_rag_agent()
    print(graph.get_graph().draw_mermaid())
