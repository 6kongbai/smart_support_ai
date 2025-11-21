from app.graphrag.nodes import planner
from app.graphrag.state import InputState


async def test_planner():
    state = InputState(question="北风商贸有哪些饮料类产品？它们的价格是多少？")
    res = await planner(state)
    print(res)
