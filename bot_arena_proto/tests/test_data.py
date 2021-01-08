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

    @staticmethod
    def test_action():
        assert Action.MOVE(Direction.UP()) == Action.MOVE(Direction.UP())
        assert Action.MOVE(Direction.UP()) != Action.MOVE(Direction.LEFT())


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

    @staticmethod
    def test_point():
        assert Point(3, 5).to_primitive() == [3, 5]
        assert Point(0, 0).to_primitive() == [0, 0]
        assert Point.from_primitive([5, 2]) == Point(5, 2)

    @staticmethod
    def test_snake_state():
        assert SnakeState(head=Point(1, 2), tail=[]).to_primitive() == {'head': [1, 2], 'tail': []}
        try:
            assert SnakeState.from_primitive({
                'head': [3, 4],
                'tail': [],
            }) == SnakeState(head=Point(3, 4), tail=[])
        except Exception as e:
            print(repr(e))
            raise

        assert SnakeState(
            head=Point(3, 7),
            tail=[Direction.UP(), Direction.UP(), Direction.RIGHT()],
        ).to_primitive() == {'head': [3, 7], 'tail': ['u', 'u', 'r']}

        assert SnakeState.from_primitive({
            'head': [8, 5],
            'tail': ['l', 'd', 'r', 'r'],
        }) == SnakeState(
            head=Point(8, 5),
            tail=[Direction.LEFT(), Direction.DOWN(), Direction.RIGHT(), Direction.RIGHT()],
        )

    @staticmethod
    def test_field_state():
        snake1 = SnakeState(head=Point(4, 2), tail=[Direction.LEFT(), Direction.UP()])
        snake2 = SnakeState(head=Point(8, 4), tail=[Direction.DOWN()])
        snake1p = snake1.to_primitive()
        snake2p = snake2.to_primitive()
        obj1 = (Point(5, 6), Object.FOOD())
        obj2 = (Point(9, 3), Object.FOOD())
        obj3 = (Point(1, 1), Object.FOOD())
        obj1p = [obj1[0].to_primitive(), obj1[1].to_primitive()]
        obj2p = [obj2[0].to_primitive(), obj2[1].to_primitive()]
        obj3p = [obj3[0].to_primitive(), obj3[1].to_primitive()]

        assert FieldState(
            snakes={'1': snake1, '2': snake2},
            objects=[obj1, obj2, obj3],
        ).to_primitive() == {'snakes': {'1': snake1p, '2': snake2p}, 'objects': [obj1p, obj2p, obj3p]}

        assert FieldState.from_primitive({
            'snakes': {'1': snake1p, '2': snake2p},
            'objects': [obj1p, obj2p, obj3p],
        }) == FieldState(
            snakes={'1': snake1, '2': snake2},
            objects=[obj1, obj2, obj3],
        )

    @staticmethod
    def test_object():
        assert Object.FOOD().to_primitive() == 'f'
        assert Object.from_primitive('f') == Object.FOOD()

    @staticmethod
    def test_action():
        assert Action.MOVE(Direction.LEFT()).to_primitive() == ['m', 'l']
        assert Action.from_primitive(['m', 'd']) == Action.MOVE(Direction.DOWN())
