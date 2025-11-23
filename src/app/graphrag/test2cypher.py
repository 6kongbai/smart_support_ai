from neo4j_graphrag.retrievers import Text2CypherRetriever

from app.db.neo4j.client import driver
from app.db.neo4j.utils import get_graph_schema
from app.llms.llm import get_chat_model

# 这里可以填写 DeepSeek 模型

# 定义用户输入：
examples = [
    "USER INPUT: '查一下订单O17的物流公司是哪个?' QUERY: MATCH (o:Order)-[:SHIPPED_VIA]->(s:Shipper) WHERE o.OrderID = 'O17' RETURN s.CompanyName",
    "USER INPUT: '查一下订单O17的物流公司电话号码' QUERY: MATCH (o:Order)-[:SHIPPED_VIA]->(s:Shipper) WHERE o.OrderID = 'O17' RETURN s.Phone",
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
