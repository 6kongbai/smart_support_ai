from langchain_core.documents import Document

from app.db.milvus.client import get_milvus
from app.db.milvus.utils import remove_milvus_collection

all_examples = {
    "产品查询": [
        {
            "question": "查询所有智能音箱类产品",
            "cypher": """MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
    WHERE c.CategoryName = '智能音箱'
    RETURN p.ProductName, p.UnitPrice, p.UnitsInStock"""
        },
        {
            "question": "查找库存少于20的产品",
            "cypher": """MATCH (p:Product)
    WHERE p.UnitsInStock < 20
    RETURN p.ProductName, p.UnitsInStock
    ORDER BY p.UnitsInStock"""
        },
        {
            "question": "哪些产品的单价高于5000元？",
            "cypher": """MATCH (p:Product)
    WHERE p.UnitPrice > 5000
    RETURN p.ProductName, p.UnitPrice
    ORDER BY p.UnitPrice DESC"""
        }
    ],
    "产品类别": [
        {
            "question": "智能家居有哪些产品类别？",
            "cypher": """MATCH (c:Category)
    RETURN c.CategoryName, c.Description"""
        },
        {
            "question": "智能灯具类别下有哪些产品？",
            "cypher": """MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
    WHERE c.CategoryName = '智能灯具'
    RETURN p.ProductName, p.UnitPrice"""
        }
    ],
    "供应商相关": [
        {
            "question": "供应商小米智能家居提供了哪些产品？",
            "cypher": """MATCH (p:Product)-[:SUPPLIED_BY]->(s:Supplier)
    WHERE s.CompanyName = '小米智能家居'
    RETURN p.ProductName, p.QuantityPerUnit, p.UnitPrice"""
        },
        {
            "question": "中国供应商提供了哪些产品？",
            "cypher": """MATCH (p:Product)-[:SUPPLIED_BY]->(s:Supplier)
    WHERE s.Country = '中国'
    RETURN s.CompanyName, p.ProductName, p.UnitPrice"""
        }
    ],
    "订单查询": [
        {
            "question": "订单O1包含哪些产品？",
            "cypher": """MATCH (o:Order)-[:CONTAINS]->(p:Product)
    WHERE o.OrderID = 'O1'
    RETURN p.ProductName, p.UnitPrice, o.OrderDate"""
        },
        {
            "question": "客户张伟下了哪些订单？",
            # 修正：使用 ContactName 而非 CustomerID 或 CompanyName
            "cypher": """MATCH (o:Order)<-[:PLACED]-(c:Customer)
    WHERE c.ContactName = '张伟'
    RETURN o.OrderID, o.OrderDate, o.Status
    ORDER BY o.OrderDate DESC"""
        },
        {
            "question": "查询所有已完成（Completed）的订单",
            # 新增：基于 Status 属性的查询
            "cypher": """MATCH (o:Order)
    WHERE o.Status = 'Completed'
    RETURN o.OrderID, o.OrderDate, o.ShipCity
    LIMIT 5"""
        }
    ],
    "物流查询": [
        {
            "question": "订单O1是通过哪个物流公司配送的？",
            "cypher": """MATCH (o:Order)-[:SHIPPED_VIA]->(s:Shipper)
    WHERE o.OrderID = 'O1'
    RETURN s.CompanyName, s.Phone, o.ShippedDate"""
        },
        {
            "question": "帮我查一下快递单号SF101的物流状态",
            # 新增：基于 TrackingNumber 的查询
            "cypher": """MATCH (o:Order)
    WHERE o.TrackingNumber = 'SF101'
    RETURN o.OrderID, o.Status, o.CurrentLocation"""
        },
        {
            "question": "顺丰速运负责配送了哪些订单？",
            # 修正：移除了不存在的 o.ShipName，加入了 TrackingNumber
            "cypher": """MATCH (o:Order)-[:SHIPPED_VIA]->(s:Shipper)
    WHERE s.CompanyName = '顺丰速运'
    RETURN o.OrderID, o.TrackingNumber, o.ShipAddress, o.ShipCity
    LIMIT 10"""
        },
        {
            "question": "现在有哪些订单还在运输中？",
            # 新增：基于 CurrentLocation 或 Status 的模糊查询
            "cypher": """MATCH (o:Order)
    WHERE o.Status = 'Shipped' OR o.Status = 'Processing'
    RETURN o.OrderID, o.TrackingNumber, o.CurrentLocation"""
        }
    ],
    "客户查询": [
        {
            "question": "哪些客户来自北京？",
            "cypher": """MATCH (c:Customer)
    WHERE c.City = '北京'
    RETURN c.ContactName, c.Phone, c.Email"""
            # 修正：移除了 CompanyName，添加 Email
        },
        {
            "question": "客户李娜的订单都配送到哪里？",
            "cypher": """MATCH (o:Order)<-[:PLACED]-(c:Customer)
    WHERE c.ContactName = '李娜'
    RETURN o.OrderID, o.ShipAddress, o.ShipCity, o.ShipCountry"""
            # 修正：查询条件改为 ContactName
        }
    ],
    "复杂查询": [
        {
            "question": "销售最多的智能家居产品是什么？",
            "cypher": """MATCH (o:Order)-[rel:CONTAINS]->(p:Product)
    WITH p.ProductName AS product, SUM(rel.Quantity) AS total_quantity
    RETURN product, total_quantity
    ORDER BY total_quantity DESC
    LIMIT 5"""
        },
        {
            "question": "订单O1中的产品分别由哪些供应商提供？",
            "cypher": """MATCH (o:Order)-[:CONTAINS]->(p:Product)-[:SUPPLIED_BY]->(s:Supplier)
    WHERE o.OrderID = 'O1'
    RETURN p.ProductName, s.CompanyName, s.ContactName, s.Phone"""
        }
        # 删除：删除了涉及 Employee 的复杂查询
    ],
    "产品评价和使用说明": [
        {
            "question": "查询产品小米智能音箱Pro的评价",
            "cypher": """MATCH (p:Product)<-[:ABOUT]-(r:Review)
    WHERE p.ProductName = '小米 智能音箱 Pro'
    RETURN r.ReviewText, r.Rating, r.ReviewDate
    ORDER BY r.ReviewDate DESC"""
        },
        {
            "question": "哪些智能门锁产品的评价超过4.5分？",
            "cypher": """MATCH (p:Product)-[:BELONGS_TO]->(c:Category), (p)<-[:ABOUT]-(r:Review)
    WHERE c.CategoryName = '智能门锁' AND r.Rating > 4.5
    RETURN p.ProductName, AVG(r.Rating) AS 平均评分, COUNT(r) AS 评价数量
    ORDER BY 平均评分 DESC"""
        }
    ],
    "订单统计": [
        {
            "question": "每个月的订单数量统计",
            "cypher": """MATCH (o:Order)
    WITH SUBSTRING(toString(o.OrderDate), 0, 7) AS month, COUNT(o) AS order_count
    RETURN month AS 月份, order_count AS 订单数量
    ORDER BY 月份"""
            # 优化：增加了 toString() 以防 OrderDate 是 Date 类型导致 substring 报错
        },
        {
            "question": "每个类别产品的销售金额",
            "cypher": """MATCH (o:Order)-[rel:CONTAINS]->(p:Product)-[:BELONGS_TO]->(c:Category)
    WITH c.CategoryName AS category, SUM(rel.UnitPrice * rel.Quantity * (1-rel.Discount)) AS total_sales
    RETURN category AS 类别, total_sales AS 销售总额
    ORDER BY 销售总额 DESC"""
        }
    ],
    "地理分析": [
        {
            "question": "各城市的客户数量统计",
            "cypher": """MATCH (c:Customer)
    WITH c.City AS city, COUNT(c) AS customer_count
    RETURN city AS 城市, customer_count AS 客户数
    ORDER BY 客户数 DESC
    LIMIT 10"""
        },
        {
            "question": "查找每个收货城市的订单数和销售额",
            "cypher": """MATCH (o:Order)-[rel:CONTAINS]->(p:Product)
    WITH o.ShipCity AS city, COUNT(DISTINCT o) AS order_count, 
        SUM(rel.UnitPrice * rel.Quantity * (1-rel.Discount)) AS sales
    RETURN city AS 城市, order_count AS 订单数, sales AS 销售额
    ORDER BY 销售额 DESC"""
            # 修正：移除了 c.Region (Schema无此字段)，改用 o.ShipCity 进行更准确的地理维度销售统计
        }
    ]
}


def init_milvus():
    vector_store = get_milvus()

    documents = []
    for category, examples in all_examples.items():
        for ex in examples:
            doc = Document(
                page_content=ex["question"],
                metadata={
                    "cypher": ex["cypher"],
                    "category": category
                }
            )
            documents.append(doc)
    if documents:
        # add_documents 会自动调用 embedding_function 计算向量并存入 Milvus
        vector_store.add_documents(documents)
        print(f"成功插入 {len(documents)} 条示例。")


def clear_milvus():
    remove_milvus_collection("cypher")
