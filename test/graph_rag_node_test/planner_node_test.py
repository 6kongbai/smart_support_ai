from app.graphrag.nodes import planner
from app.graphrag.state import InputState


async def test_planner():
    state = InputState(question="你们家卖什么商品啊")
    res = await planner(state, config={})
    print(res)
