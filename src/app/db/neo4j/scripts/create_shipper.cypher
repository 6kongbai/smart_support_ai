UNWIND [
  {id: "S1", name: "顺丰速运", phone: "95338"},
  {id: "S2", name: "京东物流", phone: "950616"},
  {id: "S3", name: "中通快递", phone: "95311"},
  {id: "S4", name: "EMS", phone: "11183"}
] AS row
MERGE (s:Shipper {ShipperID: row.id})
SET s.CompanyName = row.name,
    s.Phone = row.phone,
    s.CreatedAt = datetime(),
    s.UpdatedAt = datetime();