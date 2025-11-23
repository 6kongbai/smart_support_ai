from langchain_core.prompts import ChatPromptTemplate

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


def create_tool_selection_prompt_template() -> ChatPromptTemplate:
    """
    Create a tool selection prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """
    system_instruction = get_prompt_template("graphrag/tool_selection")

    message = "Question: {question}"

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_instruction),
            ("human", message),
        ]
    )
