from typing import List, Dict, NamedTuple, Literal, Any, Annotated

from pydantic import BaseModel, Field


# 1. 定义模版结构元数据
class CypherTemplate(NamedTuple):
    cypher: str  # 原始 Cypher 语句
    description: str  # 给 LLM 看的语义描述 (用于路由决策)
    required_params: List[str]  # 必须从用户问题中提取的参数键名 (对应 SQL 中的 $)


# 2. 完整的模版注册表 (Single Source of Truth)
CYPHER_TEMPLATES: Dict[str, CypherTemplate] = {

    # ==================== 1. 产品类查询 (Product) ====================
    "product_by_name": CypherTemplate(
        cypher="MATCH (p:Product) WHERE p.ProductName CONTAINS $product_name RETURN p.ProductName, p.UnitPrice, p.UnitsInStock, p.CategoryName",
        description="根据【产品名称】模糊查询产品的基本信息（价格、库存、所属分类）。",
        required_params=["product_name"]
    ),
    "product_by_category": CypherTemplate(
        cypher="MATCH (p:Product)-[:BELONGS_TO]->(c:Category) WHERE c.CategoryName = $category_name RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
        description="查询指定【类别名称】下的所有产品列表。",
        required_params=["category_name"]
    ),
    "product_by_supplier": CypherTemplate(
        cypher="MATCH (p:Product)-[:SUPPLIED_BY]->(s:Supplier) WHERE s.CompanyName = $supplier_name RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
        description="查询指定【供应商】提供的所有产品。",
        required_params=["supplier_name"]
    ),
    "products_low_stock": CypherTemplate(
        cypher="MATCH (p:Product) WHERE toInteger(p.UnitsInStock) < 10 RETURN p.ProductName, p.UnitsInStock, p.CategoryName ORDER BY toInteger(p.UnitsInStock)",
        description="查询库存紧张（少于 10 件）的产品，用于补货分析。",
        required_params=[]  # 无需参数
    ),
    "products_popular": CypherTemplate(
        cypher="MATCH (p:Product)<-[:ABOUT]-(r:Review) RETURN p.ProductName, count(r) as ReviewCount, avg(toFloat(r.Rating)) as AvgRating ORDER BY ReviewCount DESC LIMIT 10",
        description="查询最受欢迎的产品（基于评论数量倒序排列的前10名）。",
        required_params=[]
    ),

    # ==================== 2. 客户类查询 (Customer) ====================
    "customer_by_name": CypherTemplate(
        cypher="MATCH (c:Customer) WHERE c.CompanyName CONTAINS $customer_name RETURN c.CompanyName, c.ContactName, c.Phone, c.Country",
        description="查询【客户】的基本联系方式和所在国家。",
        required_params=["customer_name"]
    ),
    "customer_orders": CypherTemplate(
        cypher="MATCH (c:Customer)-[:PLACED]->(o:Order) WHERE c.CompanyName = $customer_name RETURN o.orderId, o.OrderDate, o.ShippedDate",
        description="查询指定【客户】下过的所有订单ID及日期。",
        required_params=["customer_name"]
    ),
    "customer_purchase_history": CypherTemplate(
        cypher="MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product) WHERE c.CompanyName = $customer_name RETURN p.ProductName, o.OrderDate, p.UnitPrice",
        description="查询指定【客户】的历史购买详情（具体买过哪些产品）。",
        required_params=["customer_name"]
    ),

    # ==================== 3. 订单类查询 (Order) ====================
    "order_by_id": CypherTemplate(
        cypher="MATCH (o:Order) WHERE o.orderId = $order_id RETURN o.OrderDate, o.RequiredDate, o.ShippedDate, o.CustomerName",
        description="根据【订单ID】查询订单的发货状态和日期信息。",
        required_params=["order_id"]
    ),
    "order_details": CypherTemplate(
        cypher="MATCH (o:Order)-[contains:CONTAINS]->(p:Product) WHERE o.orderId = $order_id RETURN p.ProductName, contains.Quantity, contains.UnitPrice, toFloat(contains.Quantity) * toFloat(contains.UnitPrice) as TotalPrice",
        description="查询指定【订单ID】中包含的具体商品明细及总价。",
        required_params=["order_id"]
    ),
    "recent_orders": CypherTemplate(
        cypher="MATCH (o:Order) RETURN o.orderId, o.OrderDate, o.CustomerName ORDER BY o.OrderDate DESC LIMIT 10",
        description="查询最近生成的 10 个新订单。",
        required_params=[]
    ),
    "delayed_orders": CypherTemplate(
        cypher="MATCH (o:Order) WHERE o.RequiredDate < o.ShippedDate OR (o.RequiredDate < date() AND o.ShippedDate IS NULL) RETURN o.orderId, o.OrderDate, o.RequiredDate, o.ShippedDate, o.CustomerName",
        description="查询所有【延迟发货】的订单（未发货且超期，或发货日期晚于要求日期）。",
        required_params=[]
    ),

    # ==================== 4. 供应商类查询 (Supplier) ====================
    "supplier_by_country": CypherTemplate(
        cypher="MATCH (s:Supplier) WHERE s.Country = $country RETURN s.CompanyName, s.ContactName, s.Phone",
        description="查询位于指定【国家】的所有供应商。",
        required_params=["country"]
    ),
    "supplier_products": CypherTemplate(
        cypher="MATCH (s:Supplier)<-[:SUPPLIED_BY]-(p:Product) WHERE s.CompanyName = $supplier_name RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
        description="查询指定【供应商】名下的所有产品库存与价格。",
        required_params=["supplier_name"]
    ),

    # ==================== 5. 类别类查询 (Category) ====================
    "all_categories": CypherTemplate(
        cypher="MATCH (c:Category) RETURN c.CategoryName, c.Description",
        description="列出系统中所有的产品类别及其描述。",
        required_params=[]
    ),
    "category_products": CypherTemplate(
        cypher="MATCH (c:Category)<-[:BELONGS_TO]-(p:Product) WHERE c.CategoryName = $category_name RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
        description="查询属于指定【类别】的所有产品。",
        required_params=["category_name"]
    ),
    "category_product_count": CypherTemplate(
        cypher="MATCH (c:Category)<-[:BELONGS_TO]-(p:Product) RETURN c.CategoryName, count(p) as ProductCount ORDER BY ProductCount DESC",
        description="统计每个类别下包含的产品数量。",
        required_params=[]
    ),

    # ==================== 6. 评论类查询 (Review) ====================
    "product_reviews": CypherTemplate(
        cypher="MATCH (p:Product)<-[:ABOUT]-(r:Review) WHERE p.ProductName = $product_name RETURN r.CustomerName, r.Rating, r.ReviewText, r.ReviewDate ORDER BY r.ReviewDate DESC",
        description="查询指定【产品】的所有用户评价内容和评分。",
        required_params=["product_name"]
    ),
    "top_rated_products": CypherTemplate(
        cypher="MATCH (p:Product)<-[:ABOUT]-(r:Review) WITH p.ProductName as ProductName, avg(toFloat(r.Rating)) as AvgRating, count(r) as ReviewCount WHERE ReviewCount > 3 RETURN ProductName, AvgRating, ReviewCount ORDER BY AvgRating DESC LIMIT 10",
        description="查询评分最高的产品榜单（仅统计评论数大于3条的产品）。",
        required_params=[]
    ),

    # ==================== 7. 销售分析类查询 (Sales Logic) ====================
    "product_sales": CypherTemplate(
        cypher="MATCH (o:Order)-[c:CONTAINS]->(p:Product) WHERE p.ProductName = $product_name RETURN sum(toFloat(c.Quantity) * toFloat(c.UnitPrice)) as TotalSales",
        description="计算指定【产品】的历史总销售额。",
        required_params=["product_name"]
    ),
    "category_sales": CypherTemplate(
        cypher="MATCH (o:Order)-[c:CONTAINS]->(p:Product)-[:BELONGS_TO]->(cat:Category) RETURN cat.CategoryName, sum(toFloat(c.Quantity) * toFloat(c.UnitPrice)) as TotalSales ORDER BY TotalSales DESC",
        description="计算各【类别】的总销售额排行。",
        required_params=[]
    ),
    "monthly_sales": CypherTemplate(
        cypher="MATCH (o:Order)-[c:CONTAINS]->(p:Product) RETURN substring(o.OrderDate, 0, 7) as Month, sum(toFloat(c.Quantity) * toFloat(c.UnitPrice)) as Sales ORDER BY Month",
        description="按月份统计商城的整体销售趋势。",
        required_params=[]
    ),

    # ==================== 8. 智能家居特定查询 (Smart Home) ====================
    "smart_home_products": CypherTemplate(
        cypher="MATCH (p:Product)-[:BELONGS_TO]->(c:Category) WHERE c.CategoryName CONTAINS '智能' RETURN p.ProductName, p.UnitPrice, p.UnitsInStock, c.CategoryName",
        description="快速筛选所有名称中包含'智能'的类别下的产品。",
        required_params=[]
    ),
    "smart_speakers": CypherTemplate(
        cypher="MATCH (p:Product)-[:BELONGS_TO]->(c:Category) WHERE c.CategoryName = '智能音箱' RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
        description="查询【智能音箱】类别的所有产品。",
        required_params=[]
    ),
    "smart_lighting": CypherTemplate(
        cypher="MATCH (p:Product)-[:BELONGS_TO]->(c:Category) WHERE c.CategoryName = '智能照明' RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
        description="查询【智能照明】类别的所有产品。",
        required_params=[]
    )
}

# 动态生成描述文本，让 LLM 知道每个 ID 是干嘛的
_template_desc_str = "\n".join(
    [f"- {k}: {v.description})" for k, v in CYPHER_TEMPLATES.items()]
)


class PredefinedCypherInput(BaseModel):
    """
    预定义业务查询工具。
    包含已经经过人工校验、准确无误的常用 Cypher 语句。

    可用模版列表：
    {template_list}
    """

    query: Annotated[
        Literal[tuple(CYPHER_TEMPLATES.keys())], Field(
            ...,
            description="从上述列表中选择最精准匹配用户意图cypher模板。"
        )
    ]



# 注入动态描述
PredefinedCypherInput.__doc__ = PredefinedCypherInput.__doc__.format(template_list=_template_desc_str)


class WebSearchInput(BaseModel):
    """如果用户问的问题是关于一些实时的产品有效信息需要联网检索的话，则使用这个工具"""
    query: str = Field(..., description="搜索引擎的最佳搜索关键词")


class Text2CypherInput(BaseModel):
    """如果用户问的是关于产品价格、库存、规格等，则使用这个工具，生成Cypher查询语句进行查询"""
    query: str = Field(..., description="需要转译为 Cypher 的完整自然语言问题")


tools = [PredefinedCypherInput, WebSearchInput, Text2CypherInput]
