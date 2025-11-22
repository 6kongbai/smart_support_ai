import pytest

from app.graph.nodes import analyze_and_route_query, respond_to_general_query, get_additional_info
from app.graph.state import OverallStates, InputState


async def test_analyze_and_route_query_simple():
    fake_state = InputState(messages=[{"role": "user", "content": "你好"}])
    fake_config = {}
    result = await analyze_and_route_query(fake_state, config=fake_config)
    print(result)


async def test_respond_to_general_query():
    fake_state = InputState(
        messages=[{"role": "user", "content": "你好"}],
    )
    fake_config = {}
    state = await respond_to_general_query(fake_state, config=fake_config)
    print(state)


async def test_get_additional_info():
    fake_state = InputState(
        messages=[{"role": "user", "content": "你好"}],
    )
    fake_config = {}
    state = await get_additional_info(fake_state, config=fake_config)
    print(state)
