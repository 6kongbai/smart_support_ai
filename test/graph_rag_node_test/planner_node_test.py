from app.graphrag.nodes import planner
from app.graphrag.state import InputState


async def test_planner():
    state = InputState(question="我的快递单号是 SF123456，帮我查查到哪了？另外如果想退货的话政策是什么？")
    res = await planner(state, config={})
    print(res)
