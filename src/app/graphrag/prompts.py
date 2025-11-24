from langchain_core.prompts import ChatPromptTemplate

from app.graphrag.tools import CYPHER_TEMPLATES
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
            ("system", get_prompt_template("graphrag/planner")),
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
{results}
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


_template_desc_str = "\n".join(
    [f"- {k}: {v.description} (必填参数: {v.required_params})"
     for k, v in CYPHER_TEMPLATES.items()]
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

    return prompt.partial(template_desc=_template_desc_str)
