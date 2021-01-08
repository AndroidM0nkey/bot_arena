from bot_arena_proto.event import Event

import pytest


def test_basic_soundness():
    assert Event.SNAKE_DIED('Bob') == Event.SNAKE_DIED('Bob')
    assert Event.SNAKE_DIED('Bob') != Event.SNAKE_DIED('Emily')
    assert Event.SNAKE_DIED('Bob') != Event.GAME_FINISHED()
    assert Event.GAME_FINISHED() == Event.GAME_FINISHED()
    assert Event.SNAKE_DIED('A') != Event.SNAKE_DIED('a')
    assert Event.GAME_STARTED(10, 20) == Event.GAME_STARTED(10, 20)
    assert Event.GAME_STARTED(10, 20) != Event.GAME_STARTED(20, 10)


def test_basic_serde():
    assert Event.SNAKE_DIED('Mike') == Event.from_primitive(['SnakeDied', {'name': 'Mike'}])
    assert Event.SNAKE_DIED('Mike') != Event.from_primitive(['SnakeDied', {'name': 'Mike1'}])
    assert Event.SNAKE_DIED('Mike').to_primitive() == ['SnakeDied', {'name': 'Mike'}]

    assert Event.GAME_FINISHED() == Event.from_primitive(['GameFinished'])
    assert Event.GAME_FINISHED().to_primitive() == ['GameFinished']

    assert Event.GAME_STARTED(20, 15) == Event.from_primitive(['GameStarted', {'width': 20, 'height': 15}])
    assert Event.GAME_STARTED(20, 15).to_primitive() == ['GameStarted', {'width': 20, 'height': 15}]
