# 📘 **图数据库核心模型设计文档 **

### 1\. 实体 (Nodes)

| 标签 (Label) | 核心属性 (Properties) | 描述 |
| :--- | :--- | :--- |
| **Order** | `OrderID`, **`TrackingNumber`**, **`CurrentLocation`**, `Status`, `OrderDate`, `ShipAddress` | 订单核心节点，包含物流追踪信息。 |
| **Product** | `ProductID`, `ProductName`, `UnitPrice`, `UnitsInStock`, `Discontinued` | 商品信息。 |
| **Category** | `CategoryID`, `CategoryName`, `Description` | 商品分类（如：智能家居、手机）。 |
| **Supplier** | `SupplierID`, `CompanyName`, `ContactName`, `City`, `Country` | 供应商（如：小米、华为）。 |
| **Customer** | `CustomerID`, `ContactName`, `Phone`, `Email`, `City` | 下单的客户。 |
| **Shipper** | `ShipperID`, `CompanyName`, `Phone` | 物流承运商（如：顺丰、京东物流）。 |
| **Review** | `ReviewID`, `ReviewText`, `Rating`, `ReviewDate` | 用户评价。 |

-----

### 2\. 关系 (Relationships)

| 关系类型 (Type) | 方向 | 属性 (Properties) | 描述 |
| :--- | :--- | :--- | :--- |
| **SHIPPED\_VIA** | `(Order) -> (Shipper)` | 无 | 订单由哪家物流公司配送。 |
| **PLACED** | `(Customer) -> (Order)` | 无 | 客户发起了订单。 |
| **CONTAINS** | `(Order) -> (Product)` | `Quantity` (数量), `UnitPrice` (成交价), `Discount` (折扣) | 订单中包含哪些商品（明细）。 |
| **BELONGS\_TO** | `(Product) -> (Category)` | 无 | 商品属于哪个类别。 |
| **SUPPLIED\_BY** | `(Product) -> (Supplier)` | 无 | 商品由哪个供应商提供。 |
| **WROTE** | `(Customer) -> (Review)` | 无 | 客户撰写了评论。 |
| **ABOUT** | `(Review) -> (Product)` | 无 | 评论针对的是哪个商品。 |

# 1\. **核心节点模型（Nodes）**

-----

## 1.1 **Order（订单）** 【核心修改】

| 属性 | 说明 |
| :--- | :--- |
| **OrderID** | 订单唯一标识（主键） |
| **TrackingNumber** | **快递单号** (新增，例如: "SF1029384756") |
| **CurrentLocation** | **当前物流运输位置** (新增，例如: "北京市海淀区转运中心") |
| **OrderDate** | 下单时间 |
| **RequiredDate** | 要求送达时间 |
| **ShippedDate** | 实际发货时间 |
| **Freight** | 运费 |
| **ShipAddress** | 收货地址 |
| **ShipCity** | 收货城市 |
| **ShipCountry** | 收货国家 |
| **Status** | 订单状态（Pending / Processing / Shipped / Completed / Cancelled） |
| **CreatedAt** | 记录创建时间 |
| **UpdatedAt** | 记录最近更新时间 |

-----

## 1.2 **Shipper（物流商/承运人）**

| 属性 | 说明 |
| :--- | :--- |
| **ShipperID** | 物流商唯一标识（主键） |
| **CompanyName** | 公司名称（如：顺丰速运、京东物流） |
| **Phone** | 客服电话 |
| **CreatedAt** | 记录创建时间 |
| **UpdatedAt** | 记录最近更新时间 |

-----

## 1.3 **Product（商品）**

| 属性 | 说明 |
| :--- | :--- |
| **ProductID** | 商品唯一标识（主键） |
| **ProductName** | 商品名称 |
| **UnitPrice** | 当前单价 |
| **UnitsInStock** | 库存数量 |
| **UnitsOnOrder** | 锁定库存 |
| **QuantityPerUnit** | 规格单位 |
| **Discontinued** | 是否停产 |

-----

## 1.4 **Category（商品类别）**

| 属性 | 说明 |
| :--- | :--- |
| **CategoryID** | 类别唯一标识（主键） |
| **CategoryName** | 类别名称 |
| **Description** | 类别描述 |

-----

## 1.5 **Supplier（供应商）**

| 属性 | 说明 |
| :--- | :--- |
| **SupplierID** | 供应商唯一标识（主键） |
| **CompanyName** | 供应商公司名称 |
| **ContactName** | 联系人姓名 |
| **Phone** | 联系电话 |
| **Address** | 地址 |
| **City** | 城市 |
| **Country** | 国家 |

-----

## 1.6 **Customer（客户）**

| 属性 | 说明 |
| :--- | :--- |
| **CustomerID** | 客户唯一标识（主键） |
| **ContactName** | 联系人姓名 |
| **Phone** | 联系电话 |
| **Email** | 邮箱地址 |
| **Address** | 收货地址 |
| **City** | 城市 |
| **Country** | 国家/地区 |

-----

## 1.7 **Review（评论）**

| 属性 | 说明 |
| :--- | :--- |
| **ReviewID** | 评论唯一标识（主键） |
| **ReviewText** | 内容 |
| **Rating** | 评分 (1-5) |
| **ReviewDate** | 时间 |

-----

# 2\. **核心关系模型（Relationships）**

-----

## 2.1 Order → Shipper (物流关系)

```cypher
(Order)-[:SHIPPED_VIA]->(Shipper)
```

**说明：** 订单通过哪个物流公司配送。

## 2.2 Customer → Order (下单)

```cypher
(Customer)-[:PLACED]->(Order)
```

**说明：** 客户下的订单。

## 2.3 Order → Product (订单详情)

```cypher
(Order)-[:CONTAINS {
    Quantity: 2,
    UnitPrice: 59.9,
    Discount: 0
}]->(Product)
```

**说明：** 订单中包含哪些商品，以及当时的购买价格和数量。
-----

## 2.4 Product → Category (分类)

```cypher
(Product)-[:BELONGS_TO]->(Category)
```

-----

## 2.5 Product → Supplier (供货)

```cypher
(Product)-[:SUPPLIED_BY]->(Supplier)
```

-----

## 2.6 Customer → Review (写评论)

```cypher
(Customer)-[:WROTE]->(Review)
```

-----

## 2.7 Review → Product (评价商品)

```cypher
(Review)-[:ABOUT]->(Product)
```
