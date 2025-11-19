import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml


def replace_env_vars(value: str) -> str:
    """
    如果字符串以 $ 开头，则将其视为环境变量引用。
    如果环境变量不存在，则抛出 KeyError 异常。
    """
    if not isinstance(value, str):
        return value

    if value.startswith("$"):
        env_var = value[1:]
        if env_var not in os.environ:
            raise KeyError(f"Environment variable '{env_var}' is not set.")
        return os.environ[env_var]

    return value


def process_dict(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    递归处理字典，将其中的 "$ENV" 字符串替换为实际环境变量值。
    """
    if not config:
        return {}

    result = {}
    for key, value in config.items():
        if isinstance(value, dict):
            result[key] = process_dict(value)
        elif isinstance(value, str):
            result[key] = replace_env_vars(value)
        else:
            result[key] = value

    return result


def _get_config_file_path() -> str:
    """Return the absolute path to conf.yaml at project root."""
    return str((Path(__file__).parents[3] / "conf.yaml").resolve())


@lru_cache(maxsize=1)
def load_yaml_config(file_path: str | None = None) -> Dict[str, Any]:
    """
    加载 YAML 配置文件，并自动替换掉其中的环境变量引用。
    同时提供缓存功能避免重复加载。
    """
    if file_path is None:
        file_path = _get_config_file_path()
        load_yaml_config(file_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file '{file_path}' does not exist.")

    with open(file_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    processed_config = process_dict(config)
    return processed_config
