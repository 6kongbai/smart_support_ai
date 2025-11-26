from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.db.neo4j.utils import get_graph_schema
from app.prompts.template import get_prompt_template

scope_description = """
    个人电商经营范围：智能家居产品，包括但不限于：
    - 智能照明（灯泡、灯带、开关）
    - 智能安防（摄像头、门锁、传感器）
    - 智能控制（温控器、遥控器、集线器）
    - 智能音箱（语音助手、音响）
    - 智能厨电（电饭煲、冰箱、洗碗机）
    - 智能清洁（扫地机器人、洗衣机）

    不包含：服装、鞋类、体育用品、化妆品、食品等非智能家居产品。
    """


def create_guardrail_check_prompt_template() -> ChatPromptTemplate:
    """
    Create a tool selection prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """

    system_prompt = get_prompt_template(
        "safe_guardrail",
        scope_context=scope_description,
        graph_context=get_graph_schema()
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}")
    ])

    return prompt


CHECK_HALLUCINATIONS = """你是一个质量评估专员，负责检查客服回复是否仅基于数据库提供的事实。

    请对以下的回答进行评分，判断其是否完全由检索到的事实支持。
    评分标准：
    - 'yes': 回答的内容完全由上下文支持（或者当上下文中没有相关信息时，回答明确表示“不知道”或“无法回答”）。
    - 'no': 回答包含了上下文中未出现的信息（产生了幻觉），或者回答与事实相矛盾。
    
    <检索到的上下文>
    {documents}
    </检索到的上下文>
    
    <生成的回答>
    {generation}
    </生成的回答>
    """


def create_contextualize_question_prompt_template():
    contextualize_q_system_prompt = (
        "你是一个专业的对话查询重写助手。\n"
        "你的任务是结合【聊天历史】和用户的【最新提问】，将最新的提问重写为一个独立、完整的句子，"
        "使其在不依赖上下文的情况下也能被清晰理解。\n\n"
        "请严格遵守以下规则：\n"
        "1. **严禁回答问题**，你的任务仅仅是重写问题。\n"
        "2. 如果用户的最新提问已经是一个完整的句子（例如：'你好'，'再见'，或者已经包含所有关键信息），请**原样返回**，不要修改。\n"
        "3. 核心目标是补全缺失的主语或宾语（例如：将 '18812345678' 重写为 '请查询顾客手机号18812345678的所有的订单'）。\n"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    return prompt
