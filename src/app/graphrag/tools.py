from typing import List, Dict, NamedTuple

from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.loader import load_yaml_config


# 1. 定义模版结构元数据
class CypherTemplate(NamedTuple):
    cypher: str  # 原始 Cypher 语句
    description: str  # 给 LLM 看的语义描述 (用于路由决策)
    required_params: List[str]  # 必须从用户问题中提取的参数键名 (对应 SQL 中的 $)


# 2. 完整的模版注册表 (Single Source of Truth)
CYPHER_TEMPLATES: Dict[str, CypherTemplate] = {

    # ==================== 1. 产品类查询 (Product) ====================
    "product_by_name": CypherTemplate(
        cypher="""
MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
WHERE p.ProductName CONTAINS $product_name
RETURN p.ProductName, p.UnitPrice, p.UnitsInStock, c.CategoryName
""".strip(),
        description="根据【产品名称】模糊查询产品的基本信息（价格、库存、所属分类）。",
        required_params=["product_name"]
    ),

    "product_by_category": CypherTemplate(
        cypher="""
MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
WHERE c.CategoryName = $category_name
RETURN p.ProductName, p.UnitPrice, p.UnitsInStock
""".strip(),
        description="查询指定【类别名称】下的所有产品列表。",
        required_params=["category_name"]
    ),

    "product_by_supplier": CypherTemplate(
        cypher="""
MATCH (p:Product)-[:SUPPLIED_BY]->(s:Supplier)
WHERE s.CompanyName = $supplier_name
RETURN p.ProductName, p.UnitPrice, p.UnitsInStock
""".strip(),
        description="查询指定【供应商】提供的所有产品。",
        required_params=["supplier_name"]
    ),

    "products_low_stock": CypherTemplate(
        cypher="""
MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
WHERE p.UnitsInStock < 10
RETURN p.ProductName, p.UnitsInStock, c.CategoryName
ORDER BY p.UnitsInStock
""".strip(),
        description="查询库存紧张（少于 10 件）的产品，用于补货分析。",
        required_params=[]
    ),

    "products_popular": CypherTemplate(
        cypher="""
MATCH (r:Review)-[:REVIEWS]->(p:Product)
RETURN p.ProductName,
       count(r) as ReviewCount,
       avg(toFloat(r.Rating)) as AvgRating
ORDER BY ReviewCount DESC
LIMIT 10
""".strip(),
        description="查询最受欢迎的产品（基于评论数量倒序排列的前10名）。",
        required_params=[]
    ),

    "products_price_range": CypherTemplate(
        cypher="""
MATCH (p:Product)
WHERE toFloat(p.UnitPrice) >= $min_price
  AND toFloat(p.UnitPrice) <= $max_price
RETURN p.ProductName, p.UnitPrice
""".strip(),
        description="查询指定【价格区间】内的产品。",
        required_params=["min_price", "max_price"]
    ),

    # ==================== 2. 客户类查询 (Customer) ====================
    "customer_by_name": CypherTemplate(
        cypher="""
MATCH (c:Customer)
WHERE c.name CONTAINS $customer_name
RETURN c.name, c.ContactName, c.Phone, c.Country
""".strip(),
        description="查询【客户】的基本联系方式和所在国家。（默认用 Customer.name 做客户名）",
        required_params=["customer_name"]
    ),

    "customer_orders": CypherTemplate(
        cypher="""
MATCH (c:Customer)-[:PLACED]->(o:Order)
WHERE c.name = $customer_name
RETURN o.OrderID, o.OrderDate, o.ShippedDate
""".strip(),
        description="查询指定【客户】下过的所有订单ID及日期。（默认用 Customer.name）",
        required_params=["customer_name"]
    ),

    "customer_purchase_history": CypherTemplate(
        cypher="""
MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)
WHERE c.name = $customer_name
RETURN p.ProductName, o.OrderDate, p.UnitPrice
""".strip(),
        description="查询指定【客户】的历史购买详情（具体买过哪些产品）。",
        required_params=["customer_name"]
    ),

    "customer_inactive": CypherTemplate(
        cypher="""
MATCH (c:Customer)-[:PLACED]->(o:Order)
WITH c, max(o.OrderDate) as LastOrder
RETURN c.name as CustomerName, LastOrder
ORDER BY LastOrder ASC
LIMIT 10
""".strip(),
        description="查询【沉睡客户】：列出最近一次下单时间最早的10位客户（可能流失）。",
        required_params=[]
    ),

    # ==================== 3. 订单与物流查询 (Order & Logistics) ====================
    "order_by_id": CypherTemplate(
        cypher="""
MATCH (c:Customer)-[:PLACED]->(o:Order)
WHERE o.OrderID = $order_id
RETURN o.OrderDate, o.RequiredDate, o.ShippedDate, c.name as CustomerName
""".strip(),
        description="根据【订单ID】查询订单的发货状态和日期信息（含客户名）。",
        required_params=["order_id"]
    ),

    "order_details": CypherTemplate(
        cypher="""
MATCH (o:Order)-[contains:CONTAINS]->(p:Product)
WHERE o.OrderID = $order_id
RETURN p.ProductName,
       contains.Quantity,
       contains.UnitPrice,
       toFloat(contains.Quantity) * toFloat(contains.UnitPrice) as TotalPrice
""".strip(),
        description="查询指定【订单ID】中包含的具体商品明细及总价。",
        required_params=["order_id"]
    ),

    "recent_orders": CypherTemplate(
        cypher="""
MATCH (c:Customer)-[:PLACED]->(o:Order)
RETURN o.OrderID, o.OrderDate, c.name as CustomerName
ORDER BY o.OrderDate DESC
LIMIT 10
""".strip(),
        description="查询最近生成的 10 个新订单（含客户名）。",
        required_params=[]
    ),

    "delayed_orders": CypherTemplate(
        cypher="""
MATCH (o:Order)
WHERE o.RequiredDate < o.ShippedDate
   OR (o.RequiredDate < date() AND o.ShippedDate IS NULL)
RETURN o.OrderID, o.OrderDate, o.RequiredDate, o.ShippedDate
""".strip(),
        description="查询所有【延迟发货】的订单。",
        required_params=[]
    ),

    "track_order": CypherTemplate(
        cypher="""
MATCH (o:Order)
WHERE o.TrackingNumber = $tracking_number
RETURN o.OrderID, o.Status, o.CurrentLocation, o.ShippedDate
""".strip(),
        description="根据【物流单号】查询包裹当前位置和状态。",
        required_params=["tracking_number"]
    ),

    "check_shipper": CypherTemplate(
        cypher="""
MATCH (o:Order)-[:SHIPPED_VIA]->(s:Shipper)
WHERE o.OrderID = $order_id
RETURN s.CompanyName, s.Phone
""".strip(),
        description="查询指定【订单】是由哪家物流公司承运的。",
        required_params=["order_id"]
    ),

    # ==================== 4. 供应商类查询 (Supplier) ====================
    "supplier_by_country": CypherTemplate(
        cypher="""
MATCH (s:Supplier)
WHERE s.Country = $country
RETURN s.CompanyName, s.ContactName, s.Phone
""".strip(),
        description="查询位于指定【国家】的所有供应商。（注意：若 Supplier 无 Country 属性需按真实字段调整）",
        required_params=["country"]
    ),

    "supplier_products": CypherTemplate(
        cypher="""
MATCH (s:Supplier)<-[:SUPPLIED_BY]-(p:Product)
WHERE s.CompanyName = $supplier_name
RETURN p.ProductName, p.UnitPrice, p.UnitsInStock
""".strip(),
        description="查询指定【供应商】名下的所有产品库存与价格。",
        required_params=["supplier_name"]
    ),

    # ==================== 5. 类别类查询 (Category) ====================
    "all_categories": CypherTemplate(
        cypher="""
MATCH (c:Category)
RETURN c.CategoryName, c.Description
""".strip(),
        description="列出系统中所有的产品类别及其描述。",
        required_params=[]
    ),

    "category_products": CypherTemplate(
        cypher="""
MATCH (c:Category)<-[:BELONGS_TO]-(p:Product)
WHERE c.CategoryName = $category_name
RETURN p.ProductName, p.UnitPrice, p.UnitsInStock
""".strip(),
        description="查询属于指定【类别】的所有产品。",
        required_params=["category_name"]
    ),

    "category_product_count": CypherTemplate(
        cypher="""
MATCH (c:Category)<-[:BELONGS_TO]-(p:Product)
RETURN c.CategoryName, count(p) as ProductCount
ORDER BY ProductCount DESC
""".strip(),
        description="统计每个类别下包含的产品数量。",
        required_params=[]
    ),

    # ==================== 6. 评论与售后查询 (Review) ====================
    "product_reviews": CypherTemplate(
        cypher="""
MATCH (c:Customer)-[:WROTE]->(r:Review)-[:REVIEWS]->(p:Product)
WHERE p.ProductName = $product_name
RETURN c.name as CustomerName, r.Rating, r.ReviewText, r.ReviewDate
ORDER BY r.ReviewDate DESC
""".strip(),
        description="查询指定【产品】的所有用户评价内容和评分。",
        required_params=["product_name"]
    ),

    "top_rated_products": CypherTemplate(
        cypher="""
MATCH (r:Review)-[:REVIEWS]->(p:Product)
WITH p.ProductName as ProductName,
     avg(toFloat(r.Rating)) as AvgRating,
     count(r) as ReviewCount
WHERE ReviewCount >= 3
RETURN ProductName, AvgRating, ReviewCount
ORDER BY AvgRating DESC
LIMIT 10
""".strip(),
        description="查询评分最高的产品榜单（仅统计评论数大于3条的产品）。",
        required_params=[]
    ),

    "negative_reviews": CypherTemplate(
        cypher="""
MATCH (r:Review)-[:REVIEWS]->(p:Product)
WHERE toFloat(r.Rating) <= 2
RETURN p.ProductName, r.Rating, r.ReviewText
ORDER BY r.ReviewDate DESC
LIMIT 10
""".strip(),
        description="查询最近的【差评】记录（评分<=2），用于售后分析。",
        required_params=[]
    ),

    # ==================== 7. 销售与折扣分析 (Sales & Promotions) ====================
    "product_sales": CypherTemplate(
        cypher="""
MATCH (o:Order)-[c:CONTAINS]->(p:Product)
WHERE p.ProductName = $product_name
RETURN sum(toFloat(c.Quantity) * toFloat(c.UnitPrice)) as TotalSales
""".strip(),
        description="计算指定【产品】的历史总销售额。",
        required_params=["product_name"]
    ),

    "category_sales": CypherTemplate(
        cypher="""
MATCH (o:Order)-[c:CONTAINS]->(p:Product)-[:BELONGS_TO]->(cat:Category)
RETURN cat.CategoryName,
       sum(toFloat(c.Quantity) * toFloat(c.UnitPrice)) as TotalSales
ORDER BY TotalSales DESC
""".strip(),
        description="计算各【类别】的总销售额排行。",
        required_params=[]
    ),

    "monthly_sales": CypherTemplate(
        cypher="""
MATCH (o:Order)-[c:CONTAINS]->(p:Product)
RETURN toString(o.OrderDate)[0..7] as Month,
       sum(toFloat(c.Quantity) * toFloat(c.UnitPrice)) as Sales
ORDER BY Month
""".strip(),
        description="按月份统计商城的整体销售趋势。",
        required_params=[]
    ),

    "discounted_products": CypherTemplate(
        cypher="""
MATCH (o:Order)-[c:CONTAINS]->(p:Product)
WHERE toFloat(c.Discount) > 0
RETURN distinct p.ProductName, c.UnitPrice, c.Discount
ORDER BY c.Discount DESC
LIMIT 10
""".strip(),
        description="查询历史上打折力度最大的商品。",
        required_params=[]
    ),

    # ==================== 8. 图谱推荐 (Recommendation) ====================
    "recommend_co_purchase": CypherTemplate(
        cypher="""
MATCH (p:Product {ProductName: $product_name})<-[:CONTAINS]-(:Order)-[:CONTAINS]->(reco:Product)
WHERE reco.ProductName <> $product_name
RETURN reco.ProductName, count(*) as Freq
ORDER BY Freq DESC
LIMIT 5
""".strip(),
        description="基于【买了又买】算法：查询买过该产品的用户通常还会购买的其他产品。",
        required_params=["product_name"]
    ),

    # ==================== 9. 智能家居特定查询 (Smart Home) ====================
    "smart_home_products": CypherTemplate(
        cypher="""
MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
WHERE c.CategoryName CONTAINS '智能'
RETURN p.ProductName, p.UnitPrice, p.UnitsInStock, c.CategoryName
""".strip(),
        description="快速筛选所有名称中包含'智能'的类别下的产品。",
        required_params=[]
    ),

    "smart_speakers": CypherTemplate(
        cypher="""
MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
WHERE c.CategoryName = '智能音箱'
RETURN p.ProductName, p.UnitPrice, p.UnitsInStock
""".strip(),
        description="查询【智能音箱】类别的所有产品。",
        required_params=[]
    ),

    "smart_lighting": CypherTemplate(
        cypher="""
MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
WHERE c.CategoryName = '智能照明'
RETURN p.ProductName, p.UnitPrice, p.UnitsInStock
""".strip(),
        description="查询【智能照明】类别的所有产品。",
        required_params=[]
    ),
}

TEMPLATE_DESC = "\n".join(
    [f"- {k}: {v.description}"
     for k, v in CYPHER_TEMPLATES.items()]
)

TEMPLATE_DESC_PARAM = "\n".join(
    [f"- {k}: {v.description} (必填参数: {v.required_params})"
     for k, v in CYPHER_TEMPLATES.items()]
)

mcp_client = MultiServerMCPClient(
    load_yaml_config().get("MCP")
)
