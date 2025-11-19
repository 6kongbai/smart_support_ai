from functools import cache

from langchain_core.language_models import BaseChatModel

from app.core.loader import load_yaml_config
from app.llms.provider import create_llm

@cache
def get_llm_by_name(name: str = None) -> BaseChatModel:
    """
    Get a language model instance by name.
    
    Args:
        name: The name of the model to retrieve. If None, uses the DEFAULT_MODEL from config.
        
    Returns:
        BaseChatModel: An instance of the requested language model.
        
    Raises:
        ValueError: If the model name is not found in configuration or if DEFAULT_MODEL 
                   is not defined when name is None.
    """
    conf = load_yaml_config()

    # Select default model
    target_name = name or conf.get("DEFAULT_MODEL")

    if not target_name:
        raise ValueError("DEFAULT_MODEL not defined in conf.yaml")
    target_name = target_name.upper()
    if name is None:
        return get_llm_by_name(target_name)

    models = conf["MODELS"]
    providers = conf["PROVIDERS"]

    if target_name not in models:
        raise ValueError(f"Model '{target_name}' not found in MODELS")

    model_conf = models[target_name]
    provider_name = model_conf["PROVIDER"]

    if provider_name not in providers:
        raise ValueError(f"Provider '{provider_name}' missing")

    # Merge local + provider configuration
    merged_conf = {**providers[provider_name], **model_conf}

    # Create LLM
    llm = create_llm(provider_name.lower(), merged_conf)

    return llm
