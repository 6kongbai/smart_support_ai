# 📘 **图数据库核心模型设计文档**

# 1. **核心节点模型（Nodes）**

---

## 1.1 **Product（商品）**

| 属性                  | 说明                            |
| ------------------- | ----------------------------- |
| **ProductID**       | 商品唯一标识（主键）                    |
| **ProductName**     | 商品名称                          |
| **UnitPrice**       | 当前单价（最新价格）                    |
| **UnitsInStock**    | 库存数量                          |
| **UnitsOnOrder**    | 已下订单但未发货数量                    |
| **QuantityPerUnit** | 商品包装单位，例如“24 - 12 oz bottles” |
| **Discontinued**    | 是否停产（true/false）              |
| **CreatedAt**       | 记录创建时间                        |
| **UpdatedAt**       | 记录最近更新时间                      |

---

## 1.2 **Category（商品类别）**

| 属性               | 说明         |
| ---------------- | ---------- |
| **CategoryID**   | 类别唯一标识（主键） |
| **CategoryName** | 类别名称       |
| **Description**  | 类别描述       |
| **CreatedAt**    | 记录创建时间     |
| **UpdatedAt**    | 记录最近更新时间   |

---

## 1.3 **Supplier（供应商）**

| 属性              | 说明          |
|-----------------|-------------|
| **SupplierID**  | 供应商唯一标识（主键） |
| **CompanyName** | 供应商公司名称     |
| **ContactName** | 联系人姓名       |
| **Phone**       | 联系电话        |
| **Address**     | 地址          |
| **City**        | 城市          |
| **Country**     | 国家          |
| **CreatedAt**   | 记录创建时间      |
| **UpdatedAt**   | 记录最近更新时间    |

---

## 1.4 **Customer（客户）**

| 属性              | 说明            |
|-----------------|---------------|
| **CustomerID**  | 客户唯一标识（主键）    |
| **ContactName** | 联系人姓名（或消费者姓名） |
| **Phone**       | 联系电话          |
| **Email**       | 邮箱地址          |
| **Address**     | 收货地址          |
| **City**        | 城市            |
| **Country**     | 国家/地区         |
| **CreatedAt**   | 记录创建时间        |
| **UpdatedAt**   | 记录最近更新时间      |

---

## 1.5 **Order（订单）**

| 属性               | 说明                                                           |
| ---------------- | ------------------------------------------------------------ |
| **OrderID**      | 订单唯一标识（主键）                                                   |
| **OrderDate**    | 下单时间                                                         |
| **RequiredDate** | 要求送达时间                                                       |
| **ShippedDate**  | 实际发货时间                                                       |
| **Freight**      | 运费                                                           |
| **ShipAddress**  | 收货地址                                                         |
| **ShipCity**     | 收货城市                                                         |
| **ShipCountry**  | 收货国家                                                         |
| **Status**       | 订单状态（Pending / Processing / Shipped / Completed / Cancelled） |
| **CreatedAt**    | 记录创建时间                                                       |
| **UpdatedAt**    | 记录最近更新时间                                                     |

---

## 1.6 **Review（评论）**

| 属性               | 说明         |
| ---------------- | ---------- |
| **ReviewID**     | 评论唯一标识（主键） |
| **ReviewText**   | 评论文本内容     |
| **Rating**       | 用户评分（1–5）  |
| **ReviewDate**   | 评论时间       |
| **HelpfulVotes** | 有用投票数      |
| **CreatedAt**    | 记录创建时间     |
| **UpdatedAt**    | 记录最近更新时间   |

---

# 2. **核心关系模型（Relationships）**

关系本身无需属性时仅列关系含义；有属性的（如订单行项目）将补充备注说明。

---

## 2.1 Product → Category

```
(Product)-[:BELONGS_TO]->(Category)
```

**说明：** 表示商品所属类别（多对一）。

---

## 2.2 Product → Supplier

```
(Product)-[:SUPPLIED_BY]->(Supplier)
```

**说明：** 表示某商品由哪个供应商提供。

---

## 2.3 Order → Product（订单行项目信息）

```
(Order)-[:CONTAINS {
    Quantity,
    UnitPrice,
    Discount
}]->(Product)
```

| 属性            | 说明               |
| ------------- | ---------------- |
| **Quantity**  | 订单中购买数量          |
| **UnitPrice** | 下单时的商品单价（锁定历史价格） |
| **Discount**  | 折扣（0–1，小数）       |

---

## 2.4 Customer → Order

```
(Customer)-[:PLACED]->(Order)
```

**说明：** 表示某客户下了哪些订单。

---

## 2.5 Customer → Review

```
(Customer)-[:WROTE]->(Review)
```

**说明：** 表示某客户写的评论。

---

## 2.6 Review → Product

```
(Review)-[:ABOUT]->(Product)
```

**说明：** 表示评论关联的商品。

---

# 3. **最终模型清单**

### Nodes

* Product（带详细商品信息）
* Category（类别定义）
* Supplier（供应商信息）
* Customer（客户信息）
* Order（订单主数据）
* Review（评价数据）

### Relationships

* Product -[:BELONGS_TO]-> Category
* Product -[:SUPPLIED_BY]-> Supplier
* Order -[:CONTAINS {Quantity, UnitPrice, Discount}]-> Product
* Customer -[:PLACED]-> Order
* Customer -[:WROTE]-> Review
* Review -[:ABOUT]-> Product
