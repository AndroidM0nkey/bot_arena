from bot_arena_proto.event import Event

import pytest


def test_basic_serde():
    assert Event(name='SnakeDied', data='Mike', must_know=False) \
        == Event.from_primitive({'name': 'SnakeDied', 'data': 'Mike', 'must_know': False})

    assert Event(name='SnakeDied', data='Mike', must_know=False).to_primitive() \
        == {'name': 'SnakeDied', 'data': 'Mike', 'must_know': False}

    assert Event(name='FooBar1', data=[{'x': True, 'y': 15}, {'x': 3}], must_know=True) \
        == Event.from_primitive(
            {'name': 'FooBar1', 'data': [{'x': True, 'y': 15}, {'x': 3}], 'must_know': True}
        )

    assert Event(name='FooBar1', data=[{'x': True, 'y': 15}, {'x': 3}], must_know=True).to_primitive() \
        == {'name': 'FooBar1', 'data': [{'x': True, 'y': 15}, {'x': 3}], 'must_know': True}
