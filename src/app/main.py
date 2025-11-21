from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from core.config import settings

llm = init_chat_model(
    model="qwen-plus",
    model_provider="openai",
    api_key=settings.DASHSCOPE_API_KEY,
    base_url=settings.DASHSCOPE_API_BASE,
    temperature=0.7,
)


def send_email(to: str, subject: str, body: str):
    """Send an email"""
    email = {
        "to": to,
        "subject": subject,
        "body": body
    }

    return f"Email sent to {to}"


agent = create_agent(
    llm,
    tools=[send_email],
    system_prompt="You are an email assistant. Always use the send_email tool.",
)
