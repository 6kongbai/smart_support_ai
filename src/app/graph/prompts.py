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


CHECK_HALLUCINATIONS = """你是一个专业的质量评估专员，负责检查客服回复是否**严格遵循**检索到的参考资料（Context）。

请根据以下规则对生成的回答进行评分：

### 评分标准
1. **事实一致性**：回答中涉及的所有**产品参数、价格、政策、功能**等事实性信息，必须都能在<检索到的上下文>中找到依据。
2. **允许推断**：如果回答是对上下文信息的合理总结或推断，应判定为支持（'yes'）。
3. **允许礼貌用语**：回答中包含的日常寒暄、礼貌用语（如“你好”、“请稍等”、“很高兴为您服务”），即使不在上下文中，也不应视为幻觉。
4. **拒绝未知**：如果上下文中没有相关信息，而回答明确表示“抱歉，暂时没有相关信息”或类似含义，应判定为支持（'yes'）。
5. **严禁编造**：如果回答包含了上下文中不存在的具体事实（例如捏造了价格或功能），必须判定为不支持（'no'）。

### 输入数据

<用户问题>
{question}
</用户问题>

<检索到的上下文>
{documents}
</检索到的上下文>

<生成的回答>
{generation}
</生成的回答>

请先进行简短的逻辑分析，然后给出评分（'yes' 或 'no'）。
    """


def create_contextualize_question_prompt_template():
    contextualize_q_system_prompt = (
        "你是一个专业的对话查询重写助手。你的任务是重写用户的最新消息，使其包含必要的上下文信息。\n\n"

        "【任务逻辑】\n"
        "1. **输入分析**：结合用户的原问题和补充信息结合助手的询问理解用户最新输入的意图。\n"
        "2. **指代消解**：如果用户输入了代词（如“它”、“这个”）或补充信息（如“O18”、“明天”），请将其与其指代的上文对象合并。\n"
        "3. **场景处理**：\n"
        "   - **如果是回答补充内容的回复**：应该结合历史对话，和用户的输入，重新写出完整的查询问题\n"
        "   - **如果是新问题**：补全缺失的主语或宾语。然后就直接返回\n"
        "   - **如果是闲聊/完整句子**：原样返回。\n\n"

        "【严格约束】\n"
        "- 重写后的句子必须以用户的意图为核心。\n"
        "- 严禁回答问题，仅输出重写后的文本。"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    return prompt


def create_intent_router_prompt_template():
    system_prompt = get_prompt_template("intent_router")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ]
    )
    return prompt


def create_general_response_prompt_template(reasoning):
    system_prompt = get_prompt_template("general_query", reasoning=reasoning)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{question}"),
        ]
    )
    return prompt


def create_get_additional_info_prompt_template(reasoning):
    system_prompt = get_prompt_template("get_additional", reasoning=reasoning)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{question}"),
        ]
    )
    return prompt
