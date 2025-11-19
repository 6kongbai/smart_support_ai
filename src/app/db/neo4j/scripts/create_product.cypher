// 最佳实践优化：使用 UNWIND 批量处理
// 1. 将数据定义为一个列表 (List of Maps)
// 2. 使用 MERGE 避免重复创建 (如果存在则匹配，不存在则创建)
// 3. 批量建立与 Category 和 Supplier 的关系

UNWIND [
  // --- Category 1: 灯具 ---
  {id: 1, name: "智能LED灯泡 A19", price: 29.9, stock: 120, order: 20, unit: "1只/盒", catID: 1, supID: 1},
  {id: 2, name: "智能LED灯泡 彩光款", price: 39.9, stock: 100, order: 30, unit: "1只/盒", catID: 1, supID: 1},
  {id: 3, name: "WiFi灯带 5米", price: 59.9, stock: 90, order: 15, unit: "5米/卷", catID: 1, supID: 4},
  {id: 4, name: "WiFi灯带 10米", price: 99.9, stock: 80, order: 10, unit: "10米/卷", catID: 1, supID: 4},
  {id: 5, name: "Zigbee灯带", price: 129.9, stock: 70, order: 15, unit: "5米/卷", catID: 1, supID: 3},
  {id: 6, name: "智能墙壁开关 单键", price: 49.9, stock: 150, order: 25, unit: "1个/盒", catID: 1, supID: 5},
  {id: 7, name: "智能墙壁开关 双键", price: 59.9, stock: 140, order: 20, unit: "1个/盒", catID: 1, supID: 5},
  {id: 8, name: "智能台灯", price: 89.9, stock: 110, order: 10, unit: "1台/盒", catID: 1, supID: 1},
  {id: 9, name: "智能落地灯", price: 159.9, stock: 50, order: 5, unit: "1台/盒", catID: 1, supID: 1},
  {id: 10, name: "自动感应夜灯", price: 19.9, stock: 200, order: 30, unit: "1个/盒", catID: 1, supID: 7},

  // --- Category 2: 安防 ---
  {id: 11, name: "室内摄像头 1080P", price: 129.0, stock: 85, order: 10, unit: "1台/盒", catID: 2, supID: 2},
  {id: 12, name: "室外摄像头 防水款", price: 199.0, stock: 70, order: 8, unit: "1台/盒", catID: 2, supID: 2},
  {id: 13, name: "云台摄像头", price: 249.0, stock: 60, order: 10, unit: "1台/盒", catID: 2, supID: 2},
  {id: 14, name: "智能门锁 指纹款", price: 899.0, stock: 45, order: 5, unit: "1套/盒", catID: 2, supID: 6},
  {id: 15, name: "智能门锁 人脸识别款", price: 1499.0, stock: 30, order: 3, unit: "1套/盒", catID: 2, supID: 6},
  {id: 16, name: "门磁传感器", price: 39.0, stock: 150, order: 20, unit: "1个/盒", catID: 2, supID: 3},
  {id: 17, name: "窗磁传感器", price: 39.0, stock: 140, order: 15, unit: "1个/盒", catID: 2, supID: 3},
  {id: 18, name: "烟雾传感器", price: 69.0, stock: 110, order: 12, unit: "1个/盒", catID: 2, supID: 3},
  {id: 19, name: "水浸传感器", price: 59.0, stock: 120, order: 10, unit: "1个/盒", catID: 2, supID: 3},
  {id: 20, name: "温湿度传感器", price: 49.0, stock: 130, order: 15, unit: "1个/盒", catID: 2, supID: 3},

  // --- Category 3: 控制 ---
  {id: 21, name: "智能温控器 标准版", price: 299.0, stock: 90, order: 10, unit: "1台/盒", catID: 3, supID: 7},
  {id: 22, name: "智能温控器 Pro版", price: 399.0, stock: 80, order: 12, unit: "1台/盒", catID: 3, supID: 7},
  {id: 23, name: "万能遥控器 mini", price: 69.0, stock: 150, order: 20, unit: "1个/盒", catID: 3, supID: 5},
  {id: 24, name: "万能遥控器 Pro", price: 129.0, stock: 130, order: 15, unit: "1个/盒", catID: 3, supID: 5},
  {id: 25, name: "Zigbee 网关", price: 159.0, stock: 110, order: 18, unit: "1个/盒", catID: 3, supID: 3},
  {id: 26, name: "WiFi 智能中枢", price: 179.0, stock: 95, order: 10, unit: "1个/盒", catID: 3, supID: 3},
  {id: 27, name: "红外控制器", price: 49.0, stock: 160, order: 20, unit: "1个/盒", catID: 3, supID: 5},
  {id: 28, name: "智能墙控面板", price: 99.0, stock: 120, order: 15, unit: "1个/盒", catID: 3, supID: 4},

  // --- Category 4: 影音 ---
  {id: 29, name: "语音助手 Mini", price: 129.0, stock: 140, order: 20, unit: "1台/盒", catID: 4, supID: 8},
  {id: 30, name: "语音助手 标准版", price: 199.0, stock: 130, order: 15, unit: "1台/盒", catID: 4, supID: 8},
  {id: 31, name: "语音助手 Max", price: 299.0, stock: 90, order: 10, unit: "1台/盒", catID: 4, supID: 8},
  {id: 32, name: "智能音响 2.0 声道", price: 249.0, stock: 70, order: 8, unit: "1套/盒", catID: 4, supID: 8},
  {id: 33, name: "智能音响 5.1 声道", price: 599.0, stock: 50, order: 5, unit: "1套/盒", catID: 4, supID: 8},
  {id: 34, name: "智能桌面音箱", price: 159.0, stock: 100, order: 10, unit: "1台/盒", catID: 4, supID: 8},

  // --- Category 5: 厨房 ---
  {id: 35, name: "智能电饭煲 3L", price: 299.0, stock: 100, order: 15, unit: "1台/盒", catID: 5, supID: 10},
  {id: 36, name: "智能电饭煲 5L", price: 399.0, stock: 90, order: 12, unit: "1台/盒", catID: 5, supID: 10},
  {id: 37, name: "智能冰箱 300L", price: 2999.0, stock: 40, order: 5, unit: "1台/盒", catID: 5, supID: 10},
  {id: 38, name: "智能冰箱 500L", price: 3999.0, stock: 35, order: 5, unit: "1台/盒", catID: 5, supID: 10},
  {id: 39, name: "智能洗碗机 8套", price: 2999.0, stock: 30, order: 4, unit: "1台/盒", catID: 5, supID: 10},
  {id: 40, name: "智能洗碗机 12套", price: 3599.0, stock: 25, order: 3, unit: "1台/盒", catID: 5, supID: 10},
  {id: 41, name: "智能空气炸锅", price: 499.0, stock: 80, order: 10, unit: "1台/盒", catID: 5, supID: 10},
  {id: 42, name: "智能微波炉", price: 899.0, stock: 70, order: 8, unit: "1台/盒", catID: 5, supID: 10},

  // --- Category 6: 清洁 ---
  {id: 43, name: "扫地机器人 基础款", price: 999.0, stock: 100, order: 10, unit: "1台/盒", catID: 6, supID: 9},
  {id: 44, name: "扫地机器人 扫拖一体", price: 1599.0, stock: 90, order: 8, unit: "1台/盒", catID: 6, supID: 9},
  {id: 45, name: "扫地机器人 自动集尘", price: 2299.0, stock: 80, order: 8, unit: "1台/盒", catID: 6, supID: 9},
  {id: 46, name: "智能洗衣机 7kg", price: 1999.0, stock: 60, order: 5, unit: "1台/盒", catID: 6, supID: 9},
  {id: 47, name: "智能洗衣机 10kg", price: 2599.0, stock: 55, order: 5, unit: "1台/盒", catID: 6, supID: 9},
  {id: 48, name: "擦窗机器人 标准版", price: 1099.0, stock: 70, order: 7, unit: "1台/盒", catID: 6, supID: 9},
  {id: 49, name: "擦窗机器人 Pro版", price: 1599.0, stock: 60, order: 5, unit: "1台/盒", catID: 6, supID: 9},
  {id: 50, name: "智能吸尘器 手持款", price: 699.0, stock: 120, order: 12, unit: "1台/盒", catID: 6, supID: 9}
] AS item

// 步骤 1: 使用 MERGE 创建或匹配产品
MERGE (p:Product {ProductID: item.id})
SET
  p.ProductName = item.name,
  p.UnitPrice = item.price,
  p.UnitsInStock = item.stock,
  p.UnitsOnOrder = item.order,
  p.QuantityPerUnit = item.unit,
  p.Discontinued = false


// 步骤 2: 匹配已存在的分类和供应商
WITH p, item
MATCH (c:Category {CategoryID: item.catID})
MATCH (s:Supplier {SupplierID: item.supID})

// 步骤 3: 使用 MERGE 建立关系
MERGE (p)-[:BELONGS_TO]->(c)
MERGE (p)-[:SUPPLIED_BY]->(s);