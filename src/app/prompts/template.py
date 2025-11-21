# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os
from datetime import datetime
from typing import List, Any, Mapping

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langchain_core.messages import BaseMessage, SystemMessage

from app.core.logger import logger

# Initialize Jinja2 environment
current_dir = os.path.dirname(os.path.abspath(__file__))

_env = Environment(
    loader=FileSystemLoader(current_dir),
    autoescape=select_autoescape(['html', 'xml', 'md'])
)

def get_prompt_template(
        prompt_name: str,
        **kwargs
) -> str:
    try:
        # 加载模版
        template = _env.get_template(f"{prompt_name}.md")
        # 渲染文本
        return template.render(**kwargs)

    except Exception as e:
        logger.error(f"Error getting template '{prompt_name}': {e}")
        raise ValueError(f"Error getting template '{prompt_name}': {e}")


def apply_prompt_template(
        prompt_name: str,
        state: Mapping[str, Any],
        **kwargs: Any
) -> List[BaseMessage]:
    """
    Apply template variables to a prompt template and return formatted messages.

    Args:
        prompt_name: Filename without extension (e.g., "general_query")
        state: Current state dict
        **kwargs: Additional variables (like 'schema')

    Returns:
        List[BaseMessage]: A list compatible with LangChain models
    """

    # 2. 处理 State 解包 (兼容 Pydantic 和 Dict)
    state_dict = state.model_dump() if hasattr(state, "model_dump") else dict(state)

    # 合并变量：当前时间 + State数据 + 额外参数 (如 schema)
    render_vars = {
        "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
        **state_dict,
        **kwargs
    }
    try:
        # 加载模版
        template = _env.get_template(f"{prompt_name}.md")

        # 渲染文本
        system_content = template.render(**render_vars)
        return [SystemMessage(content=system_content)] + state_dict.get("messages", [])

    except Exception as e:
        logger.error(f"Error applying template '{prompt_name}': {e}")
        raise ValueError(f"Error applying template '{prompt_name}': {e}")
