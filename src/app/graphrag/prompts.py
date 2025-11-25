from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime

from app.graphrag.tools import CYPHER_TEMPLATES, TEMPLATE_DESC, TEMPLATE_DESC_PARAM
from app.prompts.template import get_prompt_template


def create_planner_prompt_template() -> ChatPromptTemplate:
    """
    Create a planner prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """
    message = """{question}"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", get_prompt_template("graphrag/planner", TEMPLATE_DESC=TEMPLATE_DESC)),
            ("human", message)
        ]
    )


def create_summarization_prompt_template() -> ChatPromptTemplate:
    """
    创建一个优化后的智能电商客服摘要提示模板。
    包含防幻觉机制、结构化格式控制及风格增强。

    返回
    -------
    ChatPromptTemplate
    """

    # System Prompt：定义角色、核心任务、风格指南和严格约束
    system_instruction = get_prompt_template("graphrag/summary")

    # Human Prompt：仅包含数据输入，使用XML标签隔离
    human_input = """请依据以下信息回答用户问题：
<context>
{context}
</context>

<question>
{question}
</question>
"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_instruction),
            ("human", human_input),
        ]
    )


def create_predefined_cypher_prompt_template() -> ChatPromptTemplate:
    """
    Create a tool selection prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """

    system_prompt = """
        你是一个图数据库查询助手。你的任务是将用户问题映射到以下预定义的 Cypher 模版之一。

        ### 可用模版列表：
        {template_desc}

        ### 要求：
        1. 精确匹配：必须选择语义最接近的 template_id。
        2. 参数提取：从问题中提取 required_params 指定的实体。如果问题中未提及必要参数，请仔细分析上下文或报错。
        3. 如果没有匹配的模版，template_id 请填 "NONE"。
        """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}")
    ])

    return prompt.partial(template_desc=TEMPLATE_DESC_PARAM)


def get_web_search_prompt() -> str:
    current_date = datetime.now().strftime("%Y-%m-%d")

    WEB_SEARCH_SYSTEM_PROMPT = f"""
    你是一个电商智能客服系统中的**联网搜索专家 (Web Search Worker)**。
    你的唯一任务是利用搜索工具，回答用户的一个具体问题。

    ### 核心原则 (Critical Rules)：
    1.  **必须使用工具**：对于任何关于实时信息、产品评测、新闻、政策的问题，**必须**调用搜索工具。严禁仅凭你内部的训练数据回答（那样可能是过时的）。
    2.  **客观事实**：回答必须基于工具返回的搜索结果。如果搜索结果中包含具体的数据（日期、价格、版本号），请完整保留。
    3.  **为汇总服务**：你的输出将被另一个 AI 读取。请保持**高度精炼**。
        - 不要说“根据搜索结果...”、“我找到了...”等废话。
        - 直接陈述事实。例如：“iPhone 15 发布于 2023年9月。”
    4.  **处理失败**：如果你尝试了多次搜索仍未找到相关信息，请直接回答“未找到相关公开信息”，不要编造。
    5.  **时间感知**：今天是 {current_date}。如果用户问“最近”、“上个月”，请基于此日期推断。

    ### 回答格式：
    请以自然语言段落形式回答，确保逻辑通顺。如果涉及多个来源的观点（例如评测有好有坏），请简要概括正反面。
    """
    return WEB_SEARCH_SYSTEM_PROMPT
