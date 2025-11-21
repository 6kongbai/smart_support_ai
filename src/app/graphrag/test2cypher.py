from neo4j_graphrag.retrievers import Text2CypherRetriever

from app.db.neo4j.client import driver
from app.db.neo4j.utils import get_graph_schema
from app.llms.llm import get_chat_model

# 这里可以填写 DeepSeek 模型

# 定义用户输入：
examples = [
    "USER INPUT: 'Which actors starred in the Matrix?' QUERY: MATCH (p:Person)-[:ACTED_IN]->(m:Movie) WHERE m.title = 'The Matrix' RETURN p.name"
]

# 初始化检索器
retriever = Text2CypherRetriever(
    driver=driver,
    llm=get_chat_model(),
    neo4j_schema=get_graph_schema(),
    examples=examples,
)

query_text = "水浸传感器还有多少个库存"
print(retriever.search(query_text=query_text))
