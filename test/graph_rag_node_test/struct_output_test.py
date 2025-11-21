from app.graphrag.types import PlannerOutput
from app.llms.llm import get_llm_by_name


def test_bind_tool():
    model = get_llm_by_name()
    model = model.with_structured_output(PlannerOutput)
    print(model)
