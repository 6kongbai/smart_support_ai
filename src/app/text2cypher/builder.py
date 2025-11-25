from langgraph.graph import StateGraph

from app.text2cypher.nodes import (
    generation_cypher,
    validate_cypher,
    validate_cypher_with_llm,
    validate_cypher_with_schema,
    correction_cypher
)
from app.text2cypher.state import OverallState, InputState, OutputState


def _build_base_graph():
    builder = StateGraph(
        OverallState,
        input_schema=InputState,
        output_schema=OutputState
    )

    builder.add_node("generation_cypher", generation_cypher)
    builder.add_node("validate_cypher", validate_cypher)
    builder.add_node("validate_cypher_with_llm", validate_cypher_with_llm)
    builder.add_node('validate_cypher_with_schema', validate_cypher_with_schema)
    builder.add_node('correction_cypher', correction_cypher)

    builder.set_entry_point('generation_cypher')
    builder.set_finish_point('correction_cypher')
    return builder


def build_text2cypher_agent():
    """Build and return the agent workflow graph without memory."""
    # build state graph
    builder = _build_base_graph()
    return builder.compile(name="Text2CypherSubGraph")


if __name__ == '__main__':
    graph = build_text2cypher_agent()
    print(graph.get_graph().draw_mermaid())
