from functools import cache
from typing import Literal, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings

from app.core.loader import load_yaml_config
from app.llms.provider import create_llm_instance

# 定义业务意图类型
LLMIntent = Literal["CHAT", "REASONING", "EMBEDDING", "ROUTER"]


@cache
def _get_model_instance(intent_or_name: str, expected_type: str):
    """
    确保整个应用生命周期内，同一个配置的模型只初始化一次。
    """
    conf = load_yaml_config()

    # 1. 解析名称：优先查 DEFAULTS
    if intent_or_name in conf.get("DEFAULTS", {}):
        target_key = conf["DEFAULTS"][intent_or_name]
    else:
        target_key = intent_or_name

    # 2. 获取模型静态配置
    if target_key not in conf["MODELS"]:
        raise ValueError(f"Model '{target_key}' not defined in MODELS config.")

    model_conf = conf["MODELS"][target_key]

    # 3. 校验类型安全
    if model_conf.get("TYPE") != expected_type:
        raise ValueError(
            f"Requesting {expected_type} but model '{target_key}' is type {model_conf.get('TYPE')}")

    # 4. 获取 Provider 配置
    provider_name = model_conf["PROVIDER"]
    if provider_name not in conf["PROVIDERS"]:
        raise ValueError(f"Provider '{provider_name}' not defined.")

    # 5. 合并配置
    # 将 target_key 作为 'model' 注入，供 provider 使用 (如果没有 MODEL_NAME 就用这个)
    merged_conf = {
        **conf["PROVIDERS"][provider_name],
        **model_conf,
        "model": target_key
    }

    # 6. 创建实例
    return create_llm_instance(provider_name, expected_type, merged_conf)


def get_chat_model(name: Optional[str] = "CHAT") -> BaseChatModel:
    """
    获取通用聊天模型。
    参数配置(如 temperature) 请在 YAML 中修改。
    """
    return _get_model_instance(name, expected_type="chat")


def get_embedding_model(name: Optional[str] = "EMBEDDING") -> Embeddings:
    """
    获取 Embedding 模型。
    """
    return _get_model_instance(name, expected_type="embedding")


def get_router_model() -> BaseChatModel:
    """
    获取路由模型。
    对应的 YAML 配置 'router-lite' 中已包含 temperature: 0。
    """
    return _get_model_instance("ROUTER", expected_type="chat")
