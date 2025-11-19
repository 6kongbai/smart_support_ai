import unittest

from neo4j import Session

from app.db.neo4j.client import with_session, get_neo4j_graph
from app.db.neo4j.init_neo4j import clear_neo4j, init_neo4j
from app.db.neo4j.utils import get_graph_schema


def test_langchain_neo4j():
    print(get_graph_schema())

def test_clear_neo4j():
    clear_neo4j()


def test_init_neo4j():
    init_neo4j()


class TestNeo4jConnection(unittest.TestCase):

    @with_session
    def test_connection(self, session: Session):
        """测试 Neo4j 是否能正常连接"""
        result = session.run("RETURN 1 AS number").single()
        self.assertEqual(result["number"], 1)
        print("✓ Neo4j 连接正常")

    @with_session
    def test_write_node(self, session: Session):
        """测试写入节点"""
        session.run("CREATE (t:TestNode {name: 'test-user'})")
        print("✓ 写入节点正常")

    @with_session
    def test_query_node(self, session: Session):
        """测试查询节点"""
        result = session.run("MATCH (t:TestNode {name:'test-user'}) RETURN t").single()
        self.assertIsNotNone(result)
        print("✓ 查询节点正常")

    @with_session
    def test_clear_database(self, session: Session):
        """清理测试数据"""
        session.run("MATCH (n:TestNode) DETACH DELETE n")
        count = session.run("MATCH (n:TestNode) RETURN count(n) AS cnt").single()["cnt"]
        self.assertEqual(count, 0)
        print("✓ 清理节点正常")
