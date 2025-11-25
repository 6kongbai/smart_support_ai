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

        ## 你必须执行以下三个核心分析步骤：

        ### Step 1. 语法审计 (Syntax Audit)
        仅检查 **Cypher 语法层面** 是否正确，包括：
        - 括号/引号是否匹配。
        - 变量是否已定义并在作用域内使用。
        - 检查函数调用语法（如 `date()`, `toInteger()` 等）。

        ### Step 2. Schema 一致性检查
        只依据给定 Schema 检查：
        - 所有节点标签 (Node Label) 是否存在。
        - 所有关系类型 (Relationship Type) 是否存在且方向正确。
        - 所有属性 (Property Key) 是否存在于对应的标签/关系上。

        ### Step 3. 过滤器提取 (Filter Extraction)
        识别查询中用于**筛选节点**的所有属性条件（位于 `MATCH` 的内联属性或 `WHERE` 子句中）。

        对于每一个过滤条件，你必须提取以下四要素：
        1. **Node Label**: 必须将变量（如 `n`）解析为它在 MATCH 中定义的实际标签（如 `Person`）。
        2. **Property Key**: 属性名。
        3. **Operator**: 使用的比较操作符。包括：`=`, `<>`, `>`, `<`, `>=`, `<=`, `IN`, `CONTAINS`, `STARTS WITH`, `ENDS WITH`。
        4. **Property Value**: 字面量值。如果是 `IN` 操作符，值应当是一个列表。

        **提取示例：**
        * **Case 1 (精确匹配)**: 
            `MATCH (p:Product {{id: 'P123'}})` 
            -> Label: `Product`, Key: `id`, Operator: `=`, Value: `'P123'`

        * **Case 2 (范围查询)**: 
            `MATCH (u:User) WHERE u.age > 18` 
            -> Label: `User`, Key: `age`, Operator: `>`, Value: `18`

        * **Case 3 (列表查询)**: 
            `MATCH (c:Category) WHERE c.name IN ['Electronics', 'Books']` 
            -> Label: `Category`, Key: `name`, Operator: `IN`, Value: `['Electronics', 'Books']`

        * **Case 4 (模糊查询)**:
            `MATCH (n:Movie) WHERE n.title CONTAINS 'Matrix'`
            -> Label: `Movie`, Key: `title`, Operator: `CONTAINS`, Value: `'Matrix'`
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
