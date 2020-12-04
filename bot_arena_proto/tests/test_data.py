from bot_arena_proto.data import Direction, Point, SnakeState, FieldState, Object, Action

import pytest


class TestBasicSoundnesss:
    @staticmethod
    def test_direction():
        # There are two lists so that we try not to compare objects with themselves (when `a is b`);
        # we rather compare different objects that are assumed to be / not to be equal (`a == b`).
        # We cannot guarantee this, however.
        elements1 = [Direction.UP(), Direction.DOWN(), Direction.LEFT(), Direction.RIGHT()]
        elements2 = [Direction.UP(), Direction.DOWN(), Direction.LEFT(), Direction.RIGHT()]
        for i, x in enumerate(elements1):
            for j, y in enumerate(elements2):
                if i == j:
                    assert x == y
                else:
                    assert x != y

    @staticmethod
    def test_points():
        assert Point(1, 2) == Point(y=2, x=1)
        assert Point(x=3, y=4) != Point(x=4, y=3)

    @staticmethod
    def test_object():
        assert Object.FOOD() == Object.FOOD()


class TestBasicSerde:
    @staticmethod
    def test_direction():
        assert Direction.UP().to_primitive() == 'u'
        assert Direction.DOWN().to_primitive() == 'd'
        assert Direction.LEFT().to_primitive() == 'l'
        assert Direction.RIGHT().to_primitive() == 'r'
        assert Direction.from_primitive('u') == Direction.UP()
        assert Direction.from_primitive('d') == Direction.DOWN()
        assert Direction.from_primitive('l') == Direction.LEFT()
        assert Direction.from_primitive('r') == Direction.RIGHT()
