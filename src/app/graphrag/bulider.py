from langgraph.graph import StateGraph

from app.graphrag.edges import distribute_tasks
from app.graphrag.nodes import planner, text2cypher_query, predefined_cypher_query, network_query

workflow = StateGraph()

workflow.add_node("planner", planner)
workflow.add_node("text2cypher_node", text2cypher_query)
workflow.add_node("predefined_node", predefined_cypher_query)
workflow.add_node("search_node", network_query)

workflow.set_entry_point("planner")

# 添加条件边：从 planner 出来后，执行 distribute_tasks
workflow.add_conditional_edges(
    "planner",
    distribute_tasks,
    ["text2cypher_node", "predefined_node", "search_node"]  # 允许的目标节点
)
