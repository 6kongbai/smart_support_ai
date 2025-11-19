import pytest

from app.prompts.template import apply_prompt_template


def test_apply_prompt_template():
    state = {
        "messages": [],
        "jump_to": "general-query",
        "hallucination": {"binary_score": "0"},
        "cause": "用户输入了普通问题",
    }
    template = apply_prompt_template("general_query", state)
    print(template)
