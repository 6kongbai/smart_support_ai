// 最佳实践优化：使用 UNWIND 批量处理评论数据
// 1. 包含评论详情、所属产品ID (pid) 以及 撰写评论的客户ID (cid)
// 2. 使用 MERGE 避免重复创建
// 3. 建立 (Review)-[:REVIEWS]->(Product) 关系
// 4. 建立 (Customer)-[:WROTE]->(Review) 关系

UNWIND [
  // --- Product 1: 智能LED灯泡 A19 ---
  {rid: "R1", text: "亮度足够，响应很快", rate: 5, date: "2024-02-01", votes: 12, pid: 1, cid: "C1"},
  {rid: "R2", text: "颜色丰富但略微有点贵", rate: 4, date: "2024-02-03", votes: 8, pid: 1, cid: "C2"},
  {rid: "R3", text: "整体满意，语音控制很好用", rate: 5, date: "2024-02-05", votes: 10, pid: 1, cid: "C3"},

  // --- Product 2: 智能LED灯泡 彩光款 ---
  {rid: "R4", text: "彩光效果特别棒", rate: 5, date: "2024-02-02", votes: 15, pid: 2, cid: "C4"},
  {rid: "R5", text: "安装方便，价格合理", rate: 4, date: "2024-02-06", votes: 6, pid: 2, cid: "C5"},
  {rid: "R6", text: "和APP配合使用很顺畅", rate: 5, date: "2024-02-07", votes: 11, pid: 2, cid: "C6"},

  // --- Product 3: WiFi灯带 5米 ---
  {rid: "R7", text: "灯带亮度高，黏性不错", rate: 5, date: "2024-02-03", votes: 9, pid: 3, cid: "C7"},
  {rid: "R8", text: "颜色很正，但稍微有点热", rate: 4, date: "2024-02-08", votes: 5, pid: 3, cid: "C8"},
  {rid: "R9", text: "整体性价比不错", rate: 4, date: "2024-02-10", votes: 7, pid: 3, cid: "C9"},

  // --- Product 4: WiFi灯带 10米 ---
  {rid: "R10", text: "范围够大，适合全屋氛围灯", rate: 5, date: "2024-02-11", votes: 14, pid: 4, cid: "C10"},
  {rid: "R11", text: "连接稳定，值得购买", rate: 5, date: "2024-02-12", votes: 8, pid: 4, cid: "C11"},
  {rid: "R12", text: "偶尔有断连情况", rate: 3, date: "2024-02-13", votes: 4, pid: 4, cid: "C12"},

  // --- Product 5: Zigbee灯带 ---
  {rid: "R13", text: "Zigbee 延迟更低，体验非常好", rate: 5, date: "2024-02-01", votes: 13, pid: 5, cid: "C13"},
  {rid: "R14", text: "亮度不错，就是有点贵", rate: 4, date: "2024-02-03", votes: 6, pid: 5, cid: "C14"},
  {rid: "R15", text: "和网关关联速度很快", rate: 5, date: "2024-02-04", votes: 9, pid: 5, cid: "C15"},

  // --- Product 6: 智能墙壁开关 单键 ---
  {rid: "R16", text: "单键控制简单易用", rate: 5, date: "2024-02-05", votes: 10, pid: 6, cid: "C16"},
  {rid: "R17", text: "安装比较容易", rate: 4, date: "2024-02-06", votes: 5, pid: 6, cid: "C17"},
  {rid: "R18", text: "做工不错，手感好", rate: 5, date: "2024-02-08", votes: 7, pid: 6, cid: "C18"},

  // --- Product 7: 智能墙壁开关 双键 ---
  {rid: "R19", text: "双键很实用，一个控灯一个控灯带", rate: 5, date: "2024-02-09", votes: 12, pid: 7, cid: "C19"},
  {rid: "R20", text: "整体不错，但接线稍微复杂", rate: 4, date: "2024-02-11", votes: 4, pid: 7, cid: "C20"},
  {rid: "R21", text: "性价比很高", rate: 5, date: "2024-02-12", votes: 8, pid: 7, cid: "C1"},

  // --- Product 8: 智能台灯 ---
  {rid: "R22", text: "台灯光线柔和，非常喜欢", rate: 5, date: "2024-02-03", votes: 10, pid: 8, cid: "C2"},
  {rid: "R23", text: "亮度可调节范围大", rate: 4, date: "2024-02-04", votes: 6, pid: 8, cid: "C3"},
  {rid: "R24", text: "APP 控制很方便", rate: 5, date: "2024-02-06", votes: 12, pid: 8, cid: "C4"},

  // --- Product 9: 智能落地灯 ---
  {rid: "R25", text: "落地灯颜值很高", rate: 5, date: "2024-02-07", votes: 15, pid: 9, cid: "C5"},
  {rid: "R26", text: "灯光颜色很漂亮", rate: 4, date: "2024-02-08", votes: 7, pid: 9, cid: "C6"},
  {rid: "R27", text: "稍微有点晃", rate: 3, date: "2024-02-10", votes: 4, pid: 9, cid: "C7"},

  // --- Product 10: 自动感应夜灯 ---
  {rid: "R28", text: "感应灵敏，夜间使用很好", rate: 5, date: "2024-02-11", votes: 14, pid: 10, cid: "C8"},
  {rid: "R29", text: "亮度合适，耐用", rate: 4, date: "2024-02-13", votes: 7, pid: 10, cid: "C9"},
  {rid: "R30", text: "有时不太灵敏", rate: 3, date: "2024-02-14", votes: 3, pid: 10, cid: "C10"},

  // --- Product 11: 室内摄像头 1080P ---
  {rid: "R31", text: "画质清晰，夜视效果也不错", rate: 5, date: "2024-02-01", votes: 18, pid: 11, cid: "C11"},
  {rid: "R32", text: "连接稳定，延迟较低", rate: 4, date: "2024-02-03", votes: 10, pid: 11, cid: "C12"},
  {rid: "R33", text: "价格稍贵，但体验很好", rate: 4, date: "2024-02-04", votes: 6, pid: 11, cid: "C13"},

  // --- Product 12: 室外摄像头 防水款 ---
  {rid: "R34", text: "防水能力强，风吹雨打都没问题", rate: 5, date: "2024-02-05", votes: 20, pid: 12, cid: "C14"},
  {rid: "R35", text: "安装稍微复杂", rate: 4, date: "2024-02-06", votes: 8, pid: 12, cid: "C15"},
  {rid: "R36", text: "整体表现不错", rate: 4, date: "2024-02-08", votes: 7, pid: 12, cid: "C16"},

  // --- Product 13: 云台摄像头 ---
  {rid: "R37", text: "云台旋转很灵敏，覆盖范围大", rate: 5, date: "2024-02-09", votes: 17, pid: 13, cid: "C17"},
  {rid: "R38", text: "可视角度广，清晰度高", rate: 5, date: "2024-02-10", votes: 12, pid: 13, cid: "C18"},
  {rid: "R39", text: "偶尔会卡顿", rate: 3, date: "2024-02-11", votes: 5, pid: 13, cid: "C19"},

  // --- Product 14: 智能门锁 指纹款 ---
  {rid: "R40", text: "指纹识别速度快，非常好用", rate: 5, date: "2024-02-02", votes: 22, pid: 14, cid: "C20"},
  {rid: "R41", text: "安装师傅很专业", rate: 4, date: "2024-02-03", votes: 11, pid: 14, cid: "C1"},
  {rid: "R42", text: "偶尔识别失败一次", rate: 3, date: "2024-02-05", votes: 4, pid: 14, cid: "C2"},

  // --- Product 15: 智能门锁 人脸识别款 ---
  {rid: "R43", text: "人脸识别非常快，科技感十足", rate: 5, date: "2024-02-06", votes: 25, pid: 15, cid: "C3"},
  {rid: "R44", text: "高端大气上档次", rate: 5, date: "2024-02-07", votes: 14, pid: 15, cid: "C4"},
  {rid: "R45", text: "稍微有点贵", rate: 4, date: "2024-02-08", votes: 6, pid: 15, cid: "C5"},

  // --- Product 16: 门磁传感器 ---
  {rid: "R46", text: "灵敏度很高，推门立即报警", rate: 5, date: "2024-02-01", votes: 16, pid: 16, cid: "C6"},
  {rid: "R47", text: "体积小巧，不占地方", rate: 4, date: "2024-02-03", votes: 7, pid: 16, cid: "C7"},
  {rid: "R48", text: "偶尔误报", rate: 3, date: "2024-02-04", votes: 3, pid: 16, cid: "C8"},

  // --- Product 17: 窗磁传感器 ---
  {rid: "R49", text: "灵敏无延迟，值得推荐", rate: 5, date: "2024-02-05", votes: 13, pid: 17, cid: "C9"},
  {rid: "R50", text: "安装简单，说明清楚", rate: 4, date: "2024-02-07", votes: 6, pid: 17, cid: "C10"},
  {rid: "R51", text: "连接偶尔会掉线", rate: 3, date: "2024-02-09", votes: 4, pid: 17, cid: "C11"},

  // --- Product 18: 烟雾传感器 ---
  {rid: "R52", text: "报警声音大，很安全", rate: 5, date: "2024-02-11", votes: 18, pid: 18, cid: "C12"},
  {rid: "R53", text: "灵敏度很高", rate: 4, date: "2024-02-12", votes: 7, pid: 18, cid: "C13"},
  {rid: "R54", text: "偶尔有误报情况", rate: 3, date: "2024-02-13", votes: 3, pid: 18, cid: "C14"},

  // --- Product 19: 水浸传感器 ---
  {rid: "R55", text: "及时提醒漏水，避免损失", rate: 5, date: "2024-02-01", votes: 19, pid: 19, cid: "C15"},
  {rid: "R56", text: "设计小巧耐用", rate: 4, date: "2024-02-03", votes: 6, pid: 19, cid: "C16"},
  {rid: "R57", text: "灵敏度一般", rate: 3, date: "2024-02-06", votes: 3, pid: 19, cid: "C17"},

  // --- Product 20: 温湿度传感器 ---
  {rid: "R58", text: "非常准确，更新快速", rate: 5, date: "2024-02-08", votes: 15, pid: 20, cid: "C18"},
  {rid: "R59", text: "性价比高，值得购买", rate: 4, date: "2024-02-10", votes: 9, pid: 20, cid: "C19"},
  {rid: "R60", text: "偶尔掉线", rate: 3, date: "2024-02-12", votes: 4, pid: 20, cid: "C20"},

  // --- Product 21: 智能温控器 标准版 ---
  {rid: "R61", text: "温控精准，调节速度快", rate: 5, date: "2024-02-01", votes: 14, pid: 21, cid: "C1"},
  {rid: "R62", text: "界面简单易懂", rate: 4, date: "2024-02-03", votes: 7, pid: 21, cid: "C2"},
  {rid: "R63", text: "整体不错，就是价格稍高", rate: 4, date: "2024-02-05", votes: 6, pid: 21, cid: "C3"},

  // --- Product 22: 智能温控器 Pro版 ---
  {rid: "R64", text: "Pro版很值得，功能更强大", rate: 5, date: "2024-02-06", votes: 18, pid: 22, cid: "C4"},
  {rid: "R65", text: "支持更多场景联动", rate: 5, date: "2024-02-08", votes: 12, pid: 22, cid: "C5"},
  {rid: "R66", text: "比标准版贵一些", rate: 4, date: "2024-02-09", votes: 5, pid: 22, cid: "C6"},

  // --- Product 23: 万能遥控器 mini ---
  {rid: "R67", text: "小巧轻便，控制范围广", rate: 5, date: "2024-02-02", votes: 11, pid: 23, cid: "C7"},
  {rid: "R68", text: "兼容性很好", rate: 4, date: "2024-02-03", votes: 6, pid: 23, cid: "C8"},
  {rid: "R69", text: "偶尔红外不准", rate: 3, date: "2024-02-04", votes: 3, pid: 23, cid: "C9"},

  // --- Product 24: 万能遥控器 Pro ---
  {rid: "R70", text: "真正的万能遥控器，几乎全兼容", rate: 5, date: "2024-02-06", votes: 20, pid: 24, cid: "C10"},
  {rid: "R71", text: "联动功能很强", rate: 5, date: "2024-02-07", votes: 13, pid: 24, cid: "C11"},
  {rid: "R72", text: "比 mini 稍大但功能强", rate: 4, date: "2024-02-08", votes: 7, pid: 24, cid: "C12"},

  // --- Product 25: Zigbee 网关 ---
  {rid: "R73", text: "延迟低，稳定性高", rate: 5, date: "2024-02-10", votes: 16, pid: 25, cid: "C13"},
  {rid: "R74", text: "支持设备多", rate: 4, date: "2024-02-11", votes: 9, pid: 25, cid: "C14"},
  {rid: "R75", text: "偶尔掉线一次", rate: 3, date: "2024-02-12", votes: 3, pid: 25, cid: "C15"},

  // --- Product 26: WiFi 智能中枢 ---
  {rid: "R76", text: "全屋控制很方便", rate: 5, date: "2024-02-01", votes: 14, pid: 26, cid: "C16"},
  {rid: "R77", text: "UI 美观好用", rate: 4, date: "2024-02-03", votes: 7, pid: 26, cid: "C17"},
  {rid: "R78", text: "希望支持更多协议", rate: 4, date: "2024-02-04", votes: 5, pid: 26, cid: "C18"},

  // --- Product 27: 红外控制器 ---
  {rid: "R79", text: "家里所有电器都能控", rate: 5, date: "2024-02-02", votes: 12, pid: 27, cid: "C19"},
  {rid: "R80", text: "红外范围大", rate: 4, date: "2024-02-04", votes: 7, pid: 27, cid: "C20"},
  {rid: "R81", text: "偶尔需要重新配对", rate: 3, date: "2024-02-06", votes: 3, pid: 27, cid: "C1"},

  // --- Product 28: 智能墙控面板 ---
  {rid: "R82", text: "触控灵敏，外观好看", rate: 5, date: "2024-02-07", votes: 15, pid: 28, cid: "C2"},
  {rid: "R83", text: "安装有点复杂", rate: 4, date: "2024-02-08", votes: 6, pid: 28, cid: "C3"},
  {rid: "R84", text: "整体不错", rate: 4, date: "2024-02-09", votes: 5, pid: 28, cid: "C4"},

  // --- Product 29: 语音助手 Mini ---
  {rid: "R85", text: "反应灵敏，识别率高", rate: 5, date: "2024-02-10", votes: 18, pid: 29, cid: "C5"},
  {rid: "R86", text: "音质不错", rate: 4, date: "2024-02-12", votes: 9, pid: 29, cid: "C6"},
  {rid: "R87", text: "低音一般", rate: 3, date: "2024-02-13", votes: 3, pid: 29, cid: "C7"},

  // --- Product 30: 语音助手 标准版 ---
  {rid: "R88", text: "语音识别更准确，比 Mini 强", rate: 5, date: "2024-02-05", votes: 16, pid: 30, cid: "C8"},
  {rid: "R89", text: "音效很好，能听歌", rate: 5, date: "2024-02-06", votes: 12, pid: 30, cid: "C9"},
  {rid: "R90", text: "比 Mini 贵一点", rate: 4, date: "2024-02-07", votes: 6, pid: 30, cid: "C10"},

  // --- Product 31: 语音助手 Max ---
  {rid: "R91", text: "Max 版音效出色，低音浑厚", rate: 5, date: "2024-02-01", votes: 22, pid: 31, cid: "C11"},
  {rid: "R92", text: "语音识别响应非常快", rate: 5, date: "2024-02-03", votes: 14, pid: 31, cid: "C12"},
  {rid: "R93", text: "比标准版贵，但更强大", rate: 4, date: "2024-02-04", votes: 6, pid: 31, cid: "C13"},

  // --- Product 32: 智能音响 2.0 声道 ---
  {rid: "R94", text: "立体声效果很好", rate: 5, date: "2024-02-05", votes: 18, pid: 32, cid: "C14"},
  {rid: "R95", text: "外观时尚", rate: 4, date: "2024-02-06", votes: 7, pid: 32, cid: "C15"},
  {rid: "R96", text: "低音略弱", rate: 3, date: "2024-02-08", votes: 3, pid: 32, cid: "C16"},

  // --- Product 33: 智能音响 5.1 声道 ---
  {rid: "R97", text: "家庭影院沉浸感强", rate: 5, date: "2024-02-09", votes: 25, pid: 33, cid: "C17"},
  {rid: "R98", text: "安装需要一点时间", rate: 4, date: "2024-02-10", votes: 9, pid: 33, cid: "C18"},
  {rid: "R99", text: "音效不错，但占地较大", rate: 4, date: "2024-02-11", votes: 5, pid: 33, cid: "C19"},

  // --- Product 34: 智能桌面音箱 ---
  {rid: "R100", text: "桌面音箱小巧好用", rate: 5, date: "2024-02-12", votes: 13, pid: 34, cid: "C20"},
  {rid: "R101", text: "适合办公室使用", rate: 4, date: "2024-02-13", votes: 6, pid: 34, cid: "C1"},
  {rid: "R102", text: "价格略高", rate: 3, date: "2024-02-14", votes: 3, pid: 34, cid: "C2"},

  // --- Product 35: 智能电饭煲 3L ---
  {rid: "R103", text: "煮饭很香，操作简单", rate: 5, date: "2024-02-01", votes: 19, pid: 35, cid: "C3"},
  {rid: "R104", text: "适合小家庭", rate: 4, date: "2024-02-02", votes: 8, pid: 35, cid: "C4"},
  {rid: "R105", text: "容量稍小", rate: 3, date: "2024-02-03", votes: 4, pid: 35, cid: "C5"},

  // --- Product 36: 智能电饭煲 5L ---
  {rid: "R106", text: "容量大，全家够用", rate: 5, date: "2024-02-04", votes: 15, pid: 36, cid: "C6"},
  {rid: "R107", text: "加热均匀", rate: 4, date: "2024-02-05", votes: 7, pid: 36, cid: "C7"},
  {rid: "R108", text: "外观不错", rate: 4, date: "2024-02-06", votes: 5, pid: 36, cid: "C8"},

  // --- Product 37: 智能冰箱 300L ---
  {rid: "R109", text: "冷藏效果好，声音轻", rate: 5, date: "2024-02-07", votes: 20, pid: 37, cid: "C9"},
  {rid: "R110", text: "空间够大", rate: 4, date: "2024-02-08", votes: 8, pid: 37, cid: "C10"},
  {rid: "R111", text: "稍微有点耗电", rate: 3, date: "2024-02-09", votes: 4, pid: 37, cid: "C11"},

  // --- Product 38: 智能冰箱 500L ---
  {rid: "R112", text: "容量巨大，适合大家庭", rate: 5, date: "2024-02-10", votes: 22, pid: 38, cid: "C12"},
  {rid: "R113", text: "制冷速度快", rate: 5, date: "2024-02-11", votes: 11, pid: 38, cid: "C13"},
  {rid: "R114", text: "体积偏大，需要空间", rate: 4, date: "2024-02-12", votes: 5, pid: 38, cid: "C14"},

  // --- Product 39: 智能洗碗机 8套 ---
  {rid: "R115", text: "洗得很干净，声音也不大", rate: 5, date: "2024-02-13", votes: 16, pid: 39, cid: "C15"},
  {rid: "R116", text: "安装方便", rate: 4, date: "2024-02-14", votes: 7, pid: 39, cid: "C16"},
  {rid: "R117", text: "碗太多时效果一般", rate: 3, date: "2024-02-15", votes: 3, pid: 39, cid: "C17"},

  // --- Product 40: 智能洗碗机 12套 ---
  {rid: "R118", text: "容量大，适合大户型", rate: 5, date: "2024-02-15", votes: 14, pid: 40, cid: "C18"},
  {rid: "R119", text: "噪音比8套稍高", rate: 4, date: "2024-02-16", votes: 6, pid: 40, cid: "C19"},
  {rid: "R120", text: "整体不错", rate: 4, date: "2024-02-17", votes: 5, pid: 40, cid: "C20"},

  // --- Product 41: 智能空气炸锅 ---
  {rid: "R121", text: "空气炸效果很好，无油更健康", rate: 5, date: "2024-02-01", votes: 17, pid: 41, cid: "C1"},
  {rid: "R122", text: "容量够用，清洗方便", rate: 4, date: "2024-02-02", votes: 7, pid: 41, cid: "C2"},
  {rid: "R123", text: "声音稍微有点大", rate: 3, date: "2024-02-03", votes: 4, pid: 41, cid: "C3"},

  // --- Product 42: 智能微波炉 ---
  {rid: "R124", text: "加热均匀，速度快", rate: 5, date: "2024-02-04", votes: 14, pid: 42, cid: "C4"},
  {rid: "R125", text: "功能很多，操作容易", rate: 4, date: "2024-02-05", votes: 6, pid: 42, cid: "C5"},
  {rid: "R126", text: "声音略大", rate: 3, date: "2024-02-06", votes: 3, pid: 42, cid: "C6"},

  // --- Product 43: 扫地机器人 基础款 ---
  {rid: "R127", text: "扫地功能不错，性价比高", rate: 5, date: "2024-02-07", votes: 20, pid: 43, cid: "C7"},
  {rid: "R128", text: "路径规划一般", rate: 4, date: "2024-02-08", votes: 8, pid: 43, cid: "C8"},
  {rid: "R129", text: "偶尔卡住", rate: 3, date: "2024-02-09", votes: 4, pid: 43, cid: "C9"},

  // --- Product 44: 扫地机器人 扫拖一体 ---
  {rid: "R130", text: "扫拖一体非常方便", rate: 5, date: "2024-02-10", votes: 22, pid: 44, cid: "C10"},
  {rid: "R131", text: "拖地效果好", rate: 4, date: "2024-02-11", votes: 7, pid: 44, cid: "C11"},
  {rid: "R132", text: "水箱容量一般", rate: 3, date: "2024-02-12", votes: 3, pid: 44, cid: "C12"},

  // --- Product 45: 扫地机器人 自动集尘 ---
  {rid: "R133", text: "自动集尘太方便了！", rate: 5, date: "2024-02-13", votes: 25, pid: 45, cid: "C13"},
  {rid: "R134", text: "集尘桶声音稍大", rate: 4, date: "2024-02-14", votes: 9, pid: 45, cid: "C14"},
  {rid: "R135", text: "价格偏高", rate: 4, date: "2024-02-15", votes: 4, pid: 45, cid: "C15"},

  // --- Product 46: 智能洗衣机 7kg ---
  {rid: "R136", text: "洗衣干净，操作简单", rate: 5, date: "2024-02-01", votes: 16, pid: 46, cid: "C16"},
  {rid: "R137", text: "噪音不大", rate: 4, date: "2024-02-02", votes: 7, pid: 46, cid: "C17"},
  {rid: "R138", text: "容量偏小", rate: 3, date: "2024-02-04", votes: 3, pid: 46, cid: "C18"},

  // --- Product 47: 智能洗衣机 10kg ---
  {rid: "R139", text: "大容量很实用", rate: 5, date: "2024-02-05", votes: 18, pid: 47, cid: "C19"},
  {rid: "R140", text: "洗得干净，低噪音", rate: 5, date: "2024-02-06", votes: 10, pid: 47, cid: "C20"},
  {rid: "R141", text: "价格有点贵", rate: 4, date: "2024-02-07", votes: 5, pid: 47, cid: "C1"},

  // --- Product 48: 擦窗机器人 标准版 ---
  {rid: "R142", text: "擦得干净，比手擦轻松多了", rate: 5, date: "2024-02-08", votes: 21, pid: 48, cid: "C2"},
  {rid: "R143", text: "吸附力强", rate: 4, date: "2024-02-09", votes: 8, pid: 48, cid: "C3"},
  {rid: "R144", text: "边角处理一般", rate: 3, date: "2024-02-10", votes: 4, pid: 48, cid: "C4"},

  // --- Product 49: 擦窗机器人 Pro版 ---
  {rid: "R145", text: "Pro版智能路线更精准", rate: 5, date: "2024-02-11", votes: 23, pid: 49, cid: "C5"},
  {rid: "R146", text: "噪音比标准版低", rate: 4, date: "2024-02-12", votes: 9, pid: 49, cid: "C6"},
  {rid: "R147", text: "价格偏高但值得", rate: 4, date: "2024-02-13", votes: 6, pid: 49, cid: "C7"},

  // --- Product 50: 智能吸尘器 手持款 ---
  {rid: "R148", text: "吸力强，手持轻便", rate: 5, date: "2024-02-14", votes: 15, pid: 50, cid: "C8"},
  {rid: "R149", text: "续航一般", rate: 4, date: "2024-02-15", votes: 7, pid: 50, cid: "C9"},
  {rid: "R150", text: "功能够用，性价比不错", rate: 4, date: "2024-02-16", votes: 6, pid: 50, cid: "C10"}
] AS row

// 步骤 1: 使用 MERGE 创建评论节点
MERGE (r:Review {ReviewID: row.rid})
ON CREATE SET
    r.ReviewText = row.text,
    r.Rating = row.rate,
    r.ReviewDate = date(row.date),
    r.HelpfulVotes = row.votes

// 步骤 2: 关联到产品 (根据 pid)
WITH r, row
MATCH (p:Product {ProductID: row.pid})
MERGE (r)-[:REVIEWS]->(p)

// 步骤 3: 关联到客户 (根据 cid)
WITH r, row
MATCH (c:Customer {CustomerID: row.cid})
MERGE (c)-[:WROTE]->(r);