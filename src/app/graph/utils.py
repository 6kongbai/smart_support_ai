from app.graph.prompts import create_guardrail_check_prompt_template, create_contextualize_question_prompt_template, \
    create_intent_router_prompt_template, create_general_response_prompt_template, \
    create_get_additional_info_prompt_template
from app.graph.types import GuardrailsOutput, Router
from app.llms.llm import get_router_model, get_chat_model


def get_guardrail_check_chain():
    prompt = create_guardrail_check_prompt_template()
    return prompt | get_router_model().with_structured_output(GuardrailsOutput)


def get_contextualize_question_chain():
    prompt = create_contextualize_question_prompt_template()
    return prompt | get_router_model()


def get_analyze_and_route_chain():
    prompt = create_intent_router_prompt_template()
    return prompt | get_router_model().with_structured_output(Router)


def get_general_chain(reasoning):
    prompt = create_general_response_prompt_template(reasoning)
    return prompt | get_chat_model()


def get_additional_chain(reasoning):
    prompt = create_get_additional_info_prompt_template(reasoning)
    return prompt | get_chat_model()
