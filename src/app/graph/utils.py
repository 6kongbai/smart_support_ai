from app.graph.prompts import create_guardrail_check_prompt_template, create_contextualize_question_prompt_template
from app.graph.types import GuardrailsOutput
from app.llms.llm import get_router_model, get_chat_model


def get_guardrail_check_chain():
    prompt = create_guardrail_check_prompt_template()
    return prompt | get_router_model().with_structured_output(GuardrailsOutput)


def get_contextualize_question_chain():
    prompt = create_contextualize_question_prompt_template()
    return prompt | get_chat_model()
