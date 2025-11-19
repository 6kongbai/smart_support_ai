from typing import Dict, Any

from langchain_core.language_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

from app.llms.dashscope import ChatDashscope


LLM_PROVIDERS: Dict[str, Any] = {}


def register_provider(name):
    def wrapper(func):
        LLM_PROVIDERS[name.lower()] = func
        return func

    return wrapper


@register_provider("dashscope")
def create_dashscope_llm(conf):
    return ChatDashscope(
        model=conf["MODEL"],
        api_key=conf["API_KEY"],
        base_url=conf.get("BASE_URL"),
        max_retries=conf.get("MAX_RETRIES", 3)
    )


@register_provider("deepseek")
def create_deepseek_llm(conf):
    return ChatDeepSeek(
        model=conf["MODEL"],
        api_key=conf["API_KEY"],
        api_base=conf.get("BASE_URL"),
        max_retries=conf.get("MAX_RETRIES", 3)
    )


@register_provider("openai")
def create_openai_llm(conf):
    return ChatOpenAI(
        model_name=conf["MODEL"],
        api_key=conf["API_KEY"],
        base_url=conf.get("BASE_URL"),
        max_retries=conf.get("MAX_RETRIES", 3)
    )


def create_llm(provider: str, conf: Dict[str, Any]) -> BaseChatModel:
    if provider not in LLM_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    return LLM_PROVIDERS[provider](conf)
