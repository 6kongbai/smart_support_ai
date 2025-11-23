from typing import List, Dict, Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSerializable
from pydantic import BaseModel

from app.graphrag.prompts import create_planner_prompt_template, create_summarization_prompt_template
from app.graphrag.types import PlannerOutput
from app.llms.llm import get_router_model, get_chat_model


def get_planner_chain() -> RunnableSerializable[dict, BaseModel]:
    llm = get_router_model()
    prompt = create_planner_prompt_template()
    return prompt | llm.with_structured_output(PlannerOutput)


def get_summarize_chain() -> RunnableSerializable[dict, str]:
    llm = get_chat_model()
    prompt = create_summarization_prompt_template()
    return prompt | llm | StrOutputParser()


def sanitize_neo4j_result(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    清洗 Neo4j 数据，将复杂对象转为字符串，确保后续 LLM 能处理且可被 JSON 序列化。
    """
    # 这里是一个简单的示例，实际项目中可能需要处理 neo4j.time.DateTime 等类型
    # 或者直接使用 json.dumps(data, default=str) 的逻辑
    sanitized = []
    for record in data:
        new_record = {}
        for k, v in record.items():
            # 将非基础类型强转为字符串，防止 datetime/node 对象导致后续序列化报错
            if not isinstance(v, (str, int, float, bool, list, dict, type(None))):
                new_record[k] = str(v)
            else:
                new_record[k] = v
        sanitized.append(new_record)
    return sanitized
