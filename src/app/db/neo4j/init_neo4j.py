import os.path
from pathlib import Path
from typing import List

from neo4j import Session, Query

from app.db.neo4j.client import with_session

cypher_dir = Path(__file__).parent / "scripts"


def split_cypher_script(script: str) -> List[str]:
    """按语句分割 Cypher 文件，并且过滤注释行"""
    lines = []
    for line in script.splitlines():
        l = line.strip()
        if not l:
            continue
        if l.startswith("//"):
            continue
        lines.append(l)

    cleaned = "\n".join(lines)
    return [s.strip() for s in cleaned.split(";") if s.strip()]


def run_cypher_file(session: Session, path: str):
    with open(path, "r", encoding="utf-8") as f:
        script = f.read()

    statements = split_cypher_script(script)

    def exec_in_tx(tx):
        for stmt in statements:
            tx.run(stmt)

    session.execute_write(exec_in_tx)


@with_session
def clear_neo4j(session: Session):
    try:
        # 删除所有约束
        constraints = session.run(Query("SHOW CONSTRAINTS"))
        for record in constraints:
            session.run(Query(f"DROP CONSTRAINT {record['name']}"))

        # 删除所有索引
        indexes = session.run(Query("SHOW INDEXES"))
        for record in indexes:
            session.run(Query(f"DROP INDEX {record['name']}"))

        # 删除所有节点和关系
        session.run(Query("MATCH (n) DETACH DELETE n"))

        print("Neo4j 已完全清空。")

    except Exception as e:
        print("清空失败:", e)


def run_supply(session, entity, entity_id_field, entity_name_field):
    cypher = f"""
    MATCH (e:{entity})
    SET e.id = e.{entity_id_field},
        e.name = e.{entity_name_field}
    """
    session.run(cypher)


@with_session
def init_neo4j(session: Session):
    # 1. 创建索引
    path = os.path.join(cypher_dir, "create_constraint.cypher")
    run_cypher_file(session, path)
    print("✓ Neo4j 初始化完成（索引 + 约束 创建成功）")

    # 2. 创建 Category 实体
    run_cypher_file(session, os.path.join(cypher_dir, "create_category.cypher"))
    run_supply(session, "Category", "CategoryID", "CategoryName")
    print("✓ Neo4j 创建 Category 实体成功")

    # 3. 创建 Supplier 实体
    run_cypher_file(session, os.path.join(cypher_dir, "create_supplier.cypher"))
    run_supply(session, "Supplier", "SupplierID", "CompanyName")
    print("✓ Neo4j 创建 Supplier 实体成功")

    # 4. 创建 Product 实体
    run_cypher_file(session, os.path.join(cypher_dir, "create_product.cypher"))
    run_supply(session, "Product", "ProductID", "ProductName")
    print("✓ Neo4j 创建 Product 实体成功")

    # 5. 创建 Customer 实体
    run_cypher_file(session, os.path.join(cypher_dir, "create_customer.cypher"))
    run_supply(session, "Customer", "CustomerID", "CompanyName")
    print("✓ Neo4j 创建 Customer 实体成功")

    # 6. 创建 Order 实体
    run_cypher_file(session, os.path.join(cypher_dir, "create_order.cypher"))
    run_supply(session, "Order", "OrderID", "OrderID")
    print("✓ Neo4j 创建 Order 实体成功")

    # 7.创建 Review 实体
    run_cypher_file(session, os.path.join(cypher_dir, "create_review.cypher"))
    run_supply(session, "Review", "ReviewID", "ReviewID")
    print("✓ Neo4j 创建 Review 实体成功")

    # 8. 创建 Order和 Product关系
    run_cypher_file(session, os.path.join(cypher_dir, "create_order_details.cypher"))
    print("✓ Neo4j 创建 Order和 Product关系成功")