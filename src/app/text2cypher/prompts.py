from langchain_core.prompts import ChatPromptTemplate


def create_text2cypher_generation_prompt_template() -> ChatPromptTemplate:
    """
    创建一个优化的 Text2Cypher 生成提示词模板。
    将 Schema 和 Few-Shot Examples 提升到 System 角色，以获得更强的生成约束。
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "你是一位专业的、安全的 Neo4j Cypher 语言翻译专家。你的任务是严格根据提供的模式信息和示例，将用户问题转换为语法正确的 Cypher 查询语句。"

                    "\n\n--- 数据库schema ---\n"
                    "{schema}\n\n"  # 提升至 System

                    "--- 示例 (Few-Shot Examples) ---\n"
                    "{examples}\n\n"  # 提升至 System

                    "--- 严格输出要求 ---\n"
                    "1. 绝对 **禁止** 在响应中包含任何前言、解释、理由或额外文本。"
                    "2. 绝对 **禁止** 在查询语句周围使用任何反引号 (```) 或其他标记。"
                    "3. 查询 **必须** 只返回 Cypher 语句本身。"
                    "4. 属性 **必须** 符合schema的定义。"
                ),
            ),
            (
                "human",
                (
                    "请根据上面的上下文，将以下用户问题转换为 Cypher 查询语句："
                    "\n\n用户问题: {question}"
                    "\n\nCypher查询:"  # 最终的指令指针
                ),
            ),
        ]
    )


def create_text2cypher_validation_prompt_template() -> ChatPromptTemplate:
    """
    创建一个文本到Cypher验证提示模板。

    返回
    -------
    ChatPromptTemplate
        提示模板。
    """

    system_template = """
        你是一位严谨的 **Neo4j Cypher 语法与逻辑审计专家**。
        你的目标是验证生成的 Cypher 查询是否符合语法、逻辑以及给定的 Schema 定义，并提取关键过滤条件。

        ### **Schema 定义**:
        <schema>
            {schema}
        </schema>
        
        你必须执行以下三个核心分析步骤：

        ### 1. 语法与逻辑审计
        * 检查括号匹配、变量作用域、关键字拼写。
        * 确认查询逻辑是否能直接回答用户的自然语言问题。

        ### 2. Schema 一致性检查
        * 验证查询中使用的所有 **节点标签 (Labels)** 是否存在于 Schema 中。
        * 验证查询中使用的所有 **关系类型 (Relationship Types)** 是否存在于 Schema 中。
        * 验证查询中使用的所有 **属性键 (Property Keys)** 是否归属于正确的节点或关系。
        
        ### 3. 过滤器提取 (Filter Extraction)
        * 识别查询中用于**缩小搜索范围**的所有特定属性条件（在 MATCH 或 WHERE 子句中）。
        * 提取这些条件，以便后续进行数据库值的存在性检查。
        * 例如：`MATCH (n:Person [name: 'Alice'])` -> 提取为 Label: Person, Key: name, Value: 'Alice'。
        * 例如：`WHERE n.status = 'Active'` -> 提取为 Label: [n的标签], Key: status, Value: 'Active'。
        
        ### 示例 (Few-Shot Learning)
        Cypher: `MATCH (p:Product) WHERE p.id = 999999 RETURN p`
        分析: Schema 中 id 是 INTEGER，Cypher 使用了 INTEGER (999999)。语法正确。
        """

    human_template = """
        请审查以下内容：

        **用户原始问题**: 
        {question}

        **待验证的 Cypher 语句**: 
        {cypher}
        """

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_template),
            ("human", human_template),
        ]
    )


def create_text2cypher_correction_prompt_template() -> ChatPromptTemplate:
    system_template = """
    你是一个自动化的 **Cypher 查询修复引擎** (Cypher Query Repair Engine)。
    你的唯一任务是接收错误的 Cypher 语句和错误日志，并输出修复后的、语法正确的 Cypher 语句。
        
    ### 核心原则 (必须严格遵守)
    1. **基于 Schema**：修复后的查询必须严格符合提供的数据库 Schema (节点标签、属性名、关系类型、属性类型)。
    2. **解决报错**：仔细分析 `Error Log`，针对性地修复语法错误或属性/关系映射错误。
    3. **零废话模式 (Strict Output)**：
       - 绝对 **禁止** 输出任何解释、道歉、前言或后缀。
       - 绝对 **禁止** 使用 Markdown 代码块标记 (如 ```cypher ... ```)。
       - **只输出** 纯文本格式的 Cypher 语句本身。
    
    --- 修复指令 ---
    如果错误是 "Property not found"，请在 Schema 中查找最相似的属性名进行替换。
    如果错误是 "Syntax Error"，请修正语法结构。
    ---

    ### **Schema 定义**:
    <schema>
    {schema}
    </schema>
    
    ### 示例 (Few-Shot Learning)
    original error cypher:
    MATCH (u:User)-[:WROTE]->(r:Review)-[:ABOUT]->(p:Product) WHERE r.score >= 4 RETURN u.fullName, p.name
    
    correct cypher:
    MATCH (u:Customer)-[:WROTE]->(r:Review)-[:REVIEWS]->(p:Product) WHERE r.Rating >= 4 RETURN u.ContactName, p.ProductName
    """

    human_template = """
    请根据以下上下文修复 Cypher 查询：

    问题是：
    {question}

    Cypher语句是：
    {cypher}

    错误是：
    {errors}

    修正后的Cypher语句：
    """

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_template),
            ("human", human_template),
        ]
    )
