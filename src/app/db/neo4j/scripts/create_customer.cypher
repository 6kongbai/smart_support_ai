UNWIND [
  {id: "C1", name: "张伟", phone: "13800000001", city: "北京", addr: "北京市海淀区xx路1号"},
  {id: "C2", name: "王芳", phone: "13800000002", city: "上海", addr: "上海市浦东新区xx路2号"},
  {id: "C3", name: "李娜", phone: "13800000003", city: "深圳", addr: "深圳市南山区xx街3号"},
  {id: "C4", name: "刘强", phone: "13800000004", city: "广州", addr: "广州市天河区xx大道4号"},
  {id: "C5", name: "陈杰", phone: "13800000005", city: "杭州", addr: "杭州市西湖区xx街5号"},
  {id: "C6", name: "杨洋", phone: "13800000006", city: "成都", addr: "成都市武侯区xx路6号"},
  {id: "C7", name: "赵敏", phone: "13800000007", city: "重庆", addr: "重庆市渝中区xx街7号"},
  {id: "C8", name: "孙涛", phone: "13800000008", city: "武汉", addr: "武汉市武昌区xx路8号"},
  {id: "C9", name: "周磊", phone: "13800000009", city: "南京", addr: "南京市鼓楼区xx路9号"},
  {id: "C10", name: "吴敏", phone: "13800000010", city: "天津", addr: "天津市和平区xx街10号"},
  {id: "C11", name: "郑琳", phone: "13800000011", city: "苏州", addr: "苏州市工业园区xx路11号"},
  {id: "C12", name: "许然", phone: "13800000012", city: "青岛", addr: "青岛市市南区xx路12号"},
  {id: "C13", name: "黄杰", phone: "13800000013", city: "厦门", addr: "厦门市思明区xx街13号"},
  {id: "C14", name: "崔娜", phone: "13800000014", city: "长沙", addr: "长沙市岳麓区xx街14号"},
  {id: "C15", name: "马强", phone: "13800000015", city: "郑州", addr: "郑州市金水区xx路15号"},
  {id: "C16", name: "丁玲", phone: "13800000016", city: "昆明", addr: "昆明市五华区xx街16号"},
  {id: "C17", name: "蒋浩", phone: "13800000017", city: "合肥", addr: "合肥市包河区xx大道17号"},
  {id: "C18", name: "曹源", phone: "13800000018", city: "大连", addr: "大连市沙河口区xx街18号"},
  {id: "C19", name: "袁媛", phone: "13800000019", city: "福州", addr: "福州市鼓楼区xx路19号"},
  {id: "C20", name: "高悦", phone: "13800000020", city: "南宁", addr: "南宁市青秀区xx街20号"}
] AS row

MERGE (c:Customer {CustomerID: row.id})
SET
    c.ContactName = row.name,
    c.Phone = row.phone,
    c.Email = toLower(row.id) + "@example.com",
    c.Address = row.addr,
    c.City = row.city,
    c.Country = "中国"