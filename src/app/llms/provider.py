from typing import Dict, Any, Callable

# Embedding Models
from langchain_community.embeddings import DashScopeEmbeddings
# Chat Models
from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.llms.dashscope import ChatDashscope

FactoryFunc = Callable[[Dict[str, Any]], Any]

CHAT_FACTORIES: Dict[str, FactoryFunc] = {}
EMBEDDING_FACTORIES: Dict[str, FactoryFunc] = {}


def register_chat(provider_name):
    def wrapper(func):
        CHAT_FACTORIES[provider_name.lower()] = func
        return func

    return wrapper


def register_embedding(provider_name):
    def wrapper(func):
        EMBEDDING_FACTORIES[provider_name.lower()] = func
        return func

    return wrapper


def _clean_params(conf: Dict[str, Any]) -> Dict[str, Any]:
    """
    参数清洗：剔除系统字段，保留模型参数 (temperature, max_tokens 等)
    """
    system_keys = {
        "API_KEY", "BASE_URL", "PROVIDER", "TYPE", "MAX_RETRIES",
        "model", "MODEL_NAME", "DEFAULTS"  # 内部使用的字段
    }
    # 过滤掉 system_keys，剩下的全部作为 kwargs 传给 LangChain
    return {k: v for k, v in conf.items() if k not in system_keys}


def _get_real_model_name(conf: Dict[str, Any]) -> str:
    """
    获取真实模型名。
    如果 YAML 中定义了 MODEL_NAME (如 router-lite 场景)，则使用之；
    否则使用 Key (即 conf['model'])。
    """
    return conf.get("MODEL_NAME") or conf["model"]


# =========================
# Chat Model Factories
# =========================

@register_chat("dashscope")
def create_dashscope_chat(conf):
    return ChatDashscope(
        model=_get_real_model_name(conf),
        api_key=conf["API_KEY"],
        base_url=conf.get("BASE_URL"),
        max_retries=conf.get("MAX_RETRIES", 3),
        **_clean_params(conf)  # 透传 YAML 中的 temperature, enable_search 等
    )


@register_chat("deepseek")
def create_deepseek_chat(conf):
    return ChatDeepSeek(
        model=_get_real_model_name(conf),
        api_key=conf["API_KEY"],
        api_base=conf.get("BASE_URL"),
        max_retries=conf.get("MAX_RETRIES", 3),
        **_clean_params(conf)
    )


@register_chat("openai")
def create_openai_chat(conf):
    return ChatOpenAI(
        model_name=_get_real_model_name(conf),
        openai_api_key=conf["API_KEY"],
        openai_api_base=conf.get("BASE_URL"),
        max_retries=conf.get("MAX_RETRIES", 3),
        **_clean_params(conf)
    )


@register_chat("gemini")
def create_gemini_chat(conf):
    return ChatGoogleGenerativeAI(
        model=_get_real_model_name(conf),
        google_api_key=conf["API_KEY"],
        **_clean_params(conf)
    )


# =========================
# Embedding Model Factories
# =========================

@register_embedding("dashscope")
def create_dashscope_embedding(conf):
    return DashScopeEmbeddings(
        model=_get_real_model_name(conf),
        dashscope_api_key=conf["API_KEY"],
    )


def create_llm_instance(provider: str, model_type: str, conf: Dict[str, Any]):
    provider = provider.lower()
    if model_type == "chat":
        if provider not in CHAT_FACTORIES:
            raise ValueError(f"Unsupported Chat provider: {provider}")
        return CHAT_FACTORIES[provider](conf)
    elif model_type == "embedding":
        if provider not in EMBEDDING_FACTORIES:
            raise ValueError(f"Unsupported Embedding provider: {provider}")
        return EMBEDDING_FACTORIES[provider](conf)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
