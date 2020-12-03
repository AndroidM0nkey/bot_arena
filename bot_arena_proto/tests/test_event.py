from bot_arena_proto.event import Event

import pytest


def test_basic_soundness():
    assert Event.SnakeDied('Bob') == Event.SnakeDied('Bob')
    assert Event.SnakeDied('Bob') != Event.SnakeDied('Emily')
    assert Event.SnakeDied('Bob') != Event.GameFinished()
    assert Event.GameFinished() == Event.GameFinished()
    assert Event.SnakeDied('A') != Event.SnakeDied('a')
    assert Event.GameStarted(10, 20) == Event.GameStarted(10, 20)
    assert Event.GameStarted(10, 20) != Event.GameStarted(20, 10)


def test_basic_serde():
    assert Event.SnakeDied('Mike') == Event.from_primitive(['SnakeDied', {'name': 'Mike'}])
    assert Event.SnakeDied('Mike') != Event.from_primitive(['SnakeDied', {'name': 'Mike1'}])
    assert Event.SnakeDied('Mike').to_primitive() == ['SnakeDied', {'name': 'Mike'}]

    assert Event.GameFinished() == Event.from_primitive(['GameFinished'])
    assert Event.GameFinished().to_primitive() == ['GameFinished']

    assert Event.GameStarted(20, 15) == Event.from_primitive(['GameStarted', {'width': 20, 'height': 15}])
    assert Event.GameStarted(20, 15).to_primitive() == ['GameStarted', {'width': 20, 'height': 15}]
