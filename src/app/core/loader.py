import os
import re
from functools import cache
from pathlib import Path
from typing import Any, Dict

import yaml

# 只匹配 ${VAR}，VAR 允许 A-Z0-9_
_ENV_PATTERN = re.compile(r"(?<!\\)\${(?P<name>[A-Z0-9_]+)}")


def replace_env_vars(value: Any, *, strict: bool = True) -> Any:
    """
    把字符串中的 ${ENV} 替换为环境变量值。
    - strict=True: 环境变量不存在则抛 KeyError
    - strict=False: 环境变量不存在则保留原样 ${ENV}
    支持转义：\\${ENV} -> ${ENV}（不替换）
    """
    if not isinstance(value, str):
        return value

    def _repl(match: re.Match) -> str:
        name = match.group("name")
        if name in os.environ:
            return os.environ[name]
        if strict:
            raise KeyError(f"Environment variable '{name}' is not set.")
        return match.group(0)  # 非严格：保留原样

    replaced = _ENV_PATTERN.sub(_repl, value)

    # 把转义的 \${VAR} 还原成 ${VAR}
    return replaced.replace(r"\${", "${")


def process_config(config: Any, *, strict: bool = True) -> Any:
    """
    递归遍历任意嵌套结构，把其中的 ${ENV} 替换成真实环境变量。
    """
    if isinstance(config, dict):
        return {k: process_config(v, strict=strict) for k, v in config.items()}

    if isinstance(config, list):
        return [process_config(v, strict=strict) for v in config]

    if isinstance(config, tuple):
        return tuple(process_config(v, strict=strict) for v in config)

    if isinstance(config, set):
        return {process_config(v, strict=strict) for v in config}

    return replace_env_vars(config, strict=strict)


def _get_config_file_path() -> str:
    """Return the absolute path to conf.yaml at project root."""
    return str((Path(__file__).parents[3] / "conf.yaml").resolve())


@cache
def load_yaml_config(file_path: str | None = None) -> Dict[str, Any]:
    """
    加载 YAML 配置文件，并自动替换掉其中的环境变量引用。
    同时提供缓存功能避免重复加载。
    """
    if file_path is None:
        file_path = _get_config_file_path()
        return load_yaml_config(file_path)

    file_path = str(Path(file_path).resolve())

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file '{file_path}' does not exist.")

    with open(file_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    processed_config = process_config(config)
    return processed_config



