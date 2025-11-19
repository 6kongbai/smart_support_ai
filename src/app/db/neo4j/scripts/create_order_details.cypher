// 最佳实践优化：使用 UNWIND 批量处理订单明细 (Order Details)
// 1. 定义订单(oid) 与 产品(pid) 的对应关系
// 2. 设置关系属性：数量(qty)、下单单价(price)、折扣(disc)
// 3. 建立 (Order)-[:CONTAINS]->(Product) 关系

UNWIND [
  // --- O1 (张伟): 智能灯泡套装 ---
  {oid: "O1", pid: 1, qty: 2, price: 29.9, disc: 0.0}, // 智能LED灯泡 A19
  {oid: "O1", pid: 6, qty: 1, price: 49.9, disc: 0.0}, // 智能墙壁开关 单键

  // --- O2 (张伟): 厨房升级 ---
  {oid: "O2", pid: 35, qty: 1, price: 299.0, disc: 0.05}, // 智能电饭煲 3L

  // --- O3 (王芳): 安防监控 ---
  {oid: "O3", pid: 11, qty: 1, price: 129.0, disc: 0.0}, // 室内摄像头
  {oid: "O3", pid: 16, qty: 3, price: 39.0, disc: 0.1},  // 门磁传感器 (买多打折)

  // --- O4 (王芳): 扫地机 ---
  {oid: "O4", pid: 43, qty: 1, price: 999.0, disc: 0.0}, // 扫地机器人 基础款

  // --- O5 (李娜): 温控 ---
  {oid: "O5", pid: 21, qty: 1, price: 299.0, disc: 0.0}, // 智能温控器

  // --- O6 (李娜): 氛围灯带 ---
  {oid: "O6", pid: 3, qty: 3, price: 59.9, disc: 0.05}, // WiFi灯带 5米

  // --- O7 (刘强): 大家电 ---
  {oid: "O7", pid: 37, qty: 1, price: 2999.0, disc: 0.1}, // 智能冰箱 300L

  // --- O8 (刘强): 影音 ---
  {oid: "O8", pid: 29, qty: 2, price: 129.0, disc: 0.0}, // 语音助手 Mini

  // --- O9 (陈杰): 智能洗衣 ---
  {oid: "O9", pid: 46, qty: 1, price: 1999.0, disc: 0.0}, // 智能洗衣机 7kg

  // --- O10 (陈杰): 灯光改造 ---
  {oid: "O10", pid: 1, qty: 5, price: 29.9, disc: 0.15}, // 批量买灯泡
  {oid: "O10", pid: 2, qty: 2, price: 39.9, disc: 0.0},  // 彩光灯泡

  // --- O11 (杨洋): 智能门锁 ---
  {oid: "O11", pid: 14, qty: 1, price: 899.0, disc: 0.05}, // 指纹锁

  // --- O12 (杨洋): 传感器 ---
  {oid: "O12", pid: 18, qty: 1, price: 69.0, disc: 0.0}, // 烟雾传感器
  {oid: "O12", pid: 19, qty: 1, price: 59.0, disc: 0.0}, // 水浸传感器

  // --- O13 (赵敏): Zigbee网络 ---
  {oid: "O13", pid: 25, qty: 1, price: 159.0, disc: 0.0}, // Zigbee 网关
  {oid: "O13", pid: 5, qty: 2, price: 129.9, disc: 0.05}, // Zigbee 灯带

  // --- O14 (赵敏): 厨房电器 ---
  {oid: "O14", pid: 41, qty: 1, price: 499.0, disc: 0.1}, // 空气炸锅

  // --- O15 (孙涛): 影音升级 ---
  {oid: "O15", pid: 30, qty: 1, price: 199.0, disc: 0.0}, // 语音助手 标准版

  // --- O16 (孙涛): 学习照明 ---
  {oid: "O16", pid: 8, qty: 1, price: 89.9, disc: 0.0}, // 智能台灯

  // --- O17 (周磊): 高层擦窗 ---
  {oid: "O17", pid: 48, qty: 1, price: 1099.0, disc: 0.0}, // 擦窗机器人

  // --- O18 (周磊): 户外监控 ---
  {oid: "O18", pid: 12, qty: 2, price: 199.0, disc: 0.1}, // 室外摄像头

  // --- O19 (吴敏): 洗碗机 ---
  {oid: "O19", pid: 39, qty: 1, price: 2999.0, disc: 0.05}, // 智能洗碗机

  // --- O20 (吴敏): 遥控器 ---
  {oid: "O20", pid: 23, qty: 1, price: 69.0, disc: 0.0}, // 万能遥控器 mini

  // --- O21 (郑琳): 全屋开关 ---
  {oid: "O21", pid: 6, qty: 6, price: 49.9, disc: 0.2}, // 单键开关 (团购价)

  // --- O22 (郑琳): 双键开关 ---
  {oid: "O22", pid: 7, qty: 2, price: 59.9, disc: 0.0},

  // --- O23 (许然): 高端清洁 ---
  {oid: "O23", pid: 44, qty: 1, price: 1599.0, disc: 0.0}, // 扫拖机器人

  // --- O24 (许然): 夜灯 ---
  {oid: "O24", pid: 10, qty: 4, price: 19.9, disc: 0.0}, // 自动感应夜灯

  // --- O25 (黄杰): 音响 ---
  {oid: "O25", pid: 32, qty: 1, price: 249.0, disc: 0.05}, // 2.0 音响

  // --- O26 (黄杰): 家庭影院 ---
  {oid: "O26", pid: 33, qty: 1, price: 599.0, disc: 0.0}, // 5.1 音响

  // --- O27 (崔娜): 电饭煲 ---
  {oid: "O27", pid: 36, qty: 1, price: 399.0, disc: 0.0}, // 5L 电饭煲

  // --- O28 (崔娜): 派对灯光 ---
  {oid: "O28", pid: 2, qty: 8, price: 39.9, disc: 0.15}, // 彩光灯泡

  // --- O29 (马强): 高端门锁 ---
  {oid: "O29", pid: 15, qty: 1, price: 1499.0, disc: 0.1}, // 人脸识别锁

  // --- O30 (马强): 中枢控制 ---
  {oid: "O30", pid: 26, qty: 1, price: 179.0, disc: 0.0}, // WiFi 中枢

  // --- O31 (丁玲): 灯带 ---
  {oid: "O31", pid: 4, qty: 2, price: 99.9, disc: 0.0}, // 10米灯带

  // --- O32 (丁玲): 传感器套装 ---
  {oid: "O32", pid: 20, qty: 3, price: 49.0, disc: 0.1}, // 温湿度传感器

  // --- O33 (蒋浩): 大冰箱 ---
  {oid: "O33", pid: 38, qty: 1, price: 3999.0, disc: 0.05}, // 500L 冰箱

  // --- O34 (蒋浩): 厨房 ---
  {oid: "O34", pid: 42, qty: 1, price: 899.0, disc: 0.0}, // 微波炉

  // --- O35 (曹源): 吸尘器 ---
  {oid: "O35", pid: 50, qty: 1, price: 699.0, disc: 0.0}, // 手持吸尘器

  // --- O36 (曹源): 擦窗 ---
  {oid: "O36", pid: 49, qty: 1, price: 1599.0, disc: 0.0}, // 擦窗 Pro

  // --- O37 (袁媛): 监控 ---
  {oid: "O37", pid: 13, qty: 2, price: 249.0, disc: 0.05}, // 云台摄像头

  // --- O38 (袁媛): 防盗 ---
  {oid: "O38", pid: 17, qty: 5, price: 39.0, disc: 0.1}, // 窗磁传感器

  // --- O39 (高悦): 温控 ---
  {oid: "O39", pid: 22, qty: 1, price: 399.0, disc: 0.0}, // 温控 Pro

  // --- O40 (高悦): 顶级扫地机 ---
  {oid: "O40", pid: 45, qty: 1, price: 2299.0, disc: 0.0}  // 自动集尘
] AS row

// 步骤 1: 匹配已存在的订单和产品
MATCH (o:Order {OrderID: row.oid})
MATCH (p:Product {ProductID: row.pid})

// 步骤 2: 使用 MERGE 建立关系并设置属性
MERGE (o)-[rel:CONTAINS]->(p)
ON CREATE SET
    rel.Quantity = row.qty,
    rel.UnitPrice = row.price,
    rel.Discount = row.disc
ON MATCH SET
    // 如果需要更新已存在的关系属性
    rel.Quantity = row.qty,
    rel.UnitPrice = row.price,
    rel.Discount = row.disc;