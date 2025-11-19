// 最佳实践优化：使用 UNWIND 批量处理订单数据
// 1. 包含订单基本信息以及所属客户ID (cid)
// 2. 使用 MERGE 确保订单不重复创建
// 3. 自动建立 (Customer)-[:PLACED]->(Order) 关系

UNWIND [
  // --- C1 北京 ---
  {oid: "O1", date: "2024-01-01", req: "2024-01-06", ship: "2024-01-04", freight: 20.5, city: "北京", addr: "北京市海淀区xx路1号", cid: "C1"},
  {oid: "O2", date: "2024-01-02", req: "2024-01-07", ship: "2024-01-05", freight: 18.2, city: "北京", addr: "北京市海淀区xx路1号", cid: "C1"},

  // --- C2 上海 ---
  {oid: "O3", date: "2024-01-03", req: "2024-01-08", ship: "2024-01-06", freight: 25.0, city: "上海", addr: "上海市浦东新区xx路2号", cid: "C2"},
  {oid: "O4", date: "2024-01-04", req: "2024-01-09", ship: "2024-01-07", freight: 19.3, city: "上海", addr: "上海市浦东新区xx路2号", cid: "C2"},

  // --- C3 深圳 ---
  {oid: "O5", date: "2024-01-05", req: "2024-01-10", ship: "2024-01-08", freight: 22.1, city: "深圳", addr: "深圳市南山区xx街3号", cid: "C3"},
  {oid: "O6", date: "2024-01-06", req: "2024-01-11", ship: "2024-01-09", freight: 21.7, city: "深圳", addr: "深圳市南山区xx街3号", cid: "C3"},

  // --- C4 广州 ---
  {oid: "O7", date: "2024-01-07", req: "2024-01-12", ship: "2024-01-10", freight: 23.5, city: "广州", addr: "广州市天河区xx大道4号", cid: "C4"},
  {oid: "O8", date: "2024-01-08", req: "2024-01-13", ship: "2024-01-11", freight: 24.0, city: "广州", addr: "广州市天河区xx大道4号", cid: "C4"},

  // --- C5 杭州 ---
  {oid: "O9", date: "2024-01-09", req: "2024-01-14", ship: "2024-01-12", freight: 17.5, city: "杭州", addr: "杭州市西湖区xx街5号", cid: "C5"},
  {oid: "O10", date: "2024-01-10", req: "2024-01-15", ship: "2024-01-13", freight: 26.6, city: "杭州", addr: "杭州市西湖区xx街5号", cid: "C5"},

  // --- C6 成都 ---
  {oid: "O11", date: "2024-01-11", req: "2024-01-16", ship: "2024-01-14", freight: 18.8, city: "成都", addr: "成都市武侯区xx路6号", cid: "C6"},
  {oid: "O12", date: "2024-01-12", req: "2024-01-17", ship: "2024-01-15", freight: 20.9, city: "成都", addr: "成都市武侯区xx路6号", cid: "C6"},

  // --- C7 重庆 ---
  {oid: "O13", date: "2024-01-13", req: "2024-01-18", ship: "2024-01-16", freight: 27.0, city: "重庆", addr: "重庆市渝中区xx街7号", cid: "C7"},
  {oid: "O14", date: "2024-01-14", req: "2024-01-19", ship: "2024-01-17", freight: 29.5, city: "重庆", addr: "重庆市渝中区xx街7号", cid: "C7"},

  // --- C8 武汉 ---
  {oid: "O15", date: "2024-01-15", req: "2024-01-20", ship: "2024-01-18", freight: 19.0, city: "武汉", addr: "武汉市武昌区xx路8号", cid: "C8"},
  {oid: "O16", date: "2024-01-16", req: "2024-01-21", ship: "2024-01-19", freight: 18.2, city: "武汉", addr: "武汉市武昌区xx路8号", cid: "C8"},

  // --- C9 南京 ---
  {oid: "O17", date: "2024-01-17", req: "2024-01-22", ship: "2024-01-20", freight: 23.1, city: "南京", addr: "南京市鼓楼区xx路9号", cid: "C9"},
  {oid: "O18", date: "2024-01-18", req: "2024-01-23", ship: "2024-01-21", freight: 21.3, city: "南京", addr: "南京市鼓楼区xx路9号", cid: "C9"},

  // --- C10 天津 ---
  {oid: "O19", date: "2024-01-19", req: "2024-01-24", ship: "2024-01-22", freight: 28.0, city: "天津", addr: "天津市和平区xx街10号", cid: "C10"},
  {oid: "O20", date: "2024-01-20", req: "2024-01-25", ship: "2024-01-23", freight: 19.4, city: "天津", addr: "天津市和平区xx街10号", cid: "C10"},

  // --- C11 苏州 ---
  {oid: "O21", date: "2024-01-21", req: "2024-01-26", ship: "2024-01-24", freight: 22.8, city: "苏州", addr: "苏州市工业园区xx路11号", cid: "C11"},
  {oid: "O22", date: "2024-01-22", req: "2024-01-27", ship: "2024-01-25", freight: 20.1, city: "苏州", addr: "苏州市工业园区xx路11号", cid: "C11"},

  // --- C12 青岛 ---
  {oid: "O23", date: "2024-01-23", req: "2024-01-28", ship: "2024-01-26", freight: 24.0, city: "青岛", addr: "青岛市市南区xx路12号", cid: "C12"},
  {oid: "O24", date: "2024-01-24", req: "2024-01-29", ship: "2024-01-27", freight: 17.9, city: "青岛", addr: "青岛市市南区xx路12号", cid: "C12"},

  // --- C13 厦门 ---
  {oid: "O25", date: "2024-01-25", req: "2024-01-30", ship: "2024-01-28", freight: 26.3, city: "厦门", addr: "厦门市思明区xx街13号", cid: "C13"},
  {oid: "O26", date: "2024-01-26", req: "2024-01-31", ship: "2024-01-29", freight: 25.7, city: "厦门", addr: "厦门市思明区xx街13号", cid: "C13"},

  // --- C14 长沙 ---
  {oid: "O27", date: "2024-01-27", req: "2024-02-01", ship: "2024-01-30", freight: 21.8, city: "长沙", addr: "长沙市岳麓区xx街14号", cid: "C14"},
  {oid: "O28", date: "2024-01-28", req: "2024-02-02", ship: "2024-01-31", freight: 20.4, city: "长沙", addr: "长沙市岳麓区xx街14号", cid: "C14"},

  // --- C15 郑州 ---
  {oid: "O29", date: "2024-01-29", req: "2024-02-03", ship: "2024-02-01", freight: 23.9, city: "郑州", addr: "郑州市金水区xx路15号", cid: "C15"},
  {oid: "O30", date: "2024-01-30", req: "2024-02-04", ship: "2024-02-02", freight: 22.2, city: "郑州", addr: "郑州市金水区xx路15号", cid: "C15"},

  // --- C16 昆明 ---
  {oid: "O31", date: "2024-01-31", req: "2024-02-05", ship: "2024-02-03", freight: 18.3, city: "昆明", addr: "昆明市五华区xx街16号", cid: "C16"},
  {oid: "O32", date: "2024-02-01", req: "2024-02-06", ship: "2024-02-04", freight: 19.7, city: "昆明", addr: "昆明市五华区xx街16号", cid: "C16"},

  // --- C17 合肥 ---
  {oid: "O33", date: "2024-02-02", req: "2024-02-07", ship: "2024-02-05", freight: 27.1, city: "合肥", addr: "合肥市包河区xx大道17号", cid: "C17"},
  {oid: "O34", date: "2024-02-03", req: "2024-02-08", ship: "2024-02-06", freight: 24.8, city: "合肥", addr: "合肥市包河区xx大道17号", cid: "C17"},

  // --- C18 大连 ---
  {oid: "O35", date: "2024-02-04", req: "2024-02-09", ship: "2024-02-07", freight: 22.6, city: "大连", addr: "大连市沙河口区xx街18号", cid: "C18"},
  {oid: "O36", date: "2024-02-05", req: "2024-02-10", ship: "2024-02-08", freight: 23.3, city: "大连", addr: "大连市沙河口区xx街18号", cid: "C18"},

  // --- C19 福州 ---
  {oid: "O37", date: "2024-02-06", req: "2024-02-11", ship: "2024-02-09", freight: 19.4, city: "福州", addr: "福州市鼓楼区xx路19号", cid: "C19"},
  {oid: "O38", date: "2024-02-07", req: "2024-02-12", ship: "2024-02-10", freight: 18.9, city: "福州", addr: "福州市鼓楼区xx路19号", cid: "C19"},

  // --- C20 南宁 ---
  {oid: "O39", date: "2024-02-08", req: "2024-02-13", ship: "2024-02-11", freight: 20.5, city: "南宁", addr: "南宁市青秀区xx街20号", cid: "C20"},
  {oid: "O40", date: "2024-02-09", req: "2024-02-14", ship: "2024-02-12", freight: 21.8, city: "南宁", addr: "南宁市青秀区xx街20号", cid: "C20"}
] AS row

// 步骤 1: 使用 MERGE 创建订单节点
MERGE (o:Order {OrderID: row.oid})
SET
    o.OrderDate = date(row.date),
    o.RequiredDate = date(row.req),
    o.ShippedDate = date(row.ship),
    o.Freight = row.freight,
    o.ShipAddress = row.addr,
    o.ShipCity = row.city,
    o.ShipCountry = "中国",
    o.Status = "Completed"


// 步骤 2: 关联到客户 (根据 cid)
WITH o, row
MATCH (c:Customer {CustomerID: row.cid})
MERGE (c)-[:PLACED]->(o);