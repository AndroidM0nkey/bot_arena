from bot_arena_server.game import (
    _Snake,
    _points_to_directions,
    _directions_to_points,
)

import pytest
from bot_arena_proto.data import Direction, Point, SnakeState


class TestSnake:
    @staticmethod
    def test_get_state_works():
        snake = _Snake(head=Point(2, 5), tail=[Direction.UP(), Direction.LEFT()])
        assert snake.get_state() == SnakeState(
            head = Point(2, 5),
            tail = [Direction.UP(), Direction.LEFT()],
        )

    @staticmethod
    def test_get_state_copies():
        snake = _Snake(head=Point(7, 3), tail=[Direction.RIGHT()])
        state_before = snake.get_state()
        snake._head.y += 1
        snake._tail.insert(0, Point(7, 3))
        assert snake._head == Point(7, 4)
        assert snake._tail == [Point(7, 3), Point(8, 3)]

        # Just to make sure subsequent get_state() works fine
        state_after = snake.get_state()
        assert state_before == SnakeState(
            head = Point(7, 3),
            tail = [Direction.RIGHT()],
        )
        assert state_after == SnakeState(
            head = Point(7, 4),
            tail = [Direction.DOWN(), Direction.RIGHT()],
        )

    @staticmethod
    def test_grow():
        snake = _Snake(head=Point(2, 4), tail=[])

        snake.grow(Direction.UP())
        assert snake.get_state() == SnakeState(
            head = Point(2, 5),
            tail = [Direction.DOWN()],
        )

        snake.grow(Direction.UP())
        assert snake.get_state() == SnakeState(
            head = Point(2, 6),
            tail = [Direction.DOWN(), Direction.DOWN()],
        )

        snake.grow(Direction.LEFT())
        assert snake.get_state() == SnakeState(
            head = Point(1, 6),
            tail = [Direction.RIGHT(), Direction.DOWN(), Direction.DOWN()],
        )

        snake.grow(Direction.DOWN())
        assert snake.get_state() == SnakeState(
            head = Point(1, 5),
            tail = [Direction.UP(), Direction.RIGHT(), Direction.DOWN(), Direction.DOWN()],
        )

        snake.grow(Direction.RIGHT())
        assert snake.get_state() == SnakeState(
            head = Point(2, 5),
            tail = [Direction.LEFT(), Direction.UP(), Direction.RIGHT(), Direction.DOWN(), Direction.DOWN()],
        )

    @staticmethod
    def test_move():
        snake = _Snake(head=Point(2, 4), tail=[Direction.RIGHT(), Direction.DOWN(), Direction.LEFT()])

        snake.move(Direction.UP())
        assert snake.get_state() == SnakeState(
            head = Point(2, 5),
            tail = [Direction.DOWN(), Direction.RIGHT(), Direction.DOWN()],
        )

        snake.move(Direction.UP())
        assert snake.get_state() == SnakeState(
            head = Point(2, 6),
            tail = [Direction.DOWN(), Direction.DOWN(), Direction.RIGHT()],
        )

        snake.move(Direction.LEFT())
        assert snake.get_state() == SnakeState(
            head = Point(1, 6),
            tail = [Direction.RIGHT(), Direction.DOWN(), Direction.DOWN()],
        )

        snake.move(Direction.DOWN())
        assert snake.get_state() == SnakeState(
            head = Point(1, 5),
            tail = [Direction.UP(), Direction.RIGHT(), Direction.DOWN()],
        )

        snake.move(Direction.RIGHT())
        assert snake.get_state() == SnakeState(
            head = Point(2, 5),
            tail = [Direction.LEFT(), Direction.UP(), Direction.RIGHT()],
        )

    @staticmethod
    def test_list_occupied_cells():
        snake = _Snake(head=Point(6, 5), tail=[Direction.UP(), Direction.LEFT(), Direction.LEFT()])
        assert set(snake.list_occupied_cells()) == {Point(6, 5), Point(6, 6), Point(5, 6), Point(4, 6)}

        snake = _Snake(head=Point(9, 4), tail=[Direction.DOWN(), Direction.RIGHT(), Direction.DOWN()])
        assert set(snake.list_occupied_cells()) == {Point(9, 4), Point(9, 3), Point(10, 3), Point(10, 2)}


def test_points_to_directions():
    h1 = Point(5, 7)
    p1 = [Point(5, 8), Point(5, 9), Point(4, 9), Point(5, 9), Point(6, 9), Point(6, 8)]
    d1 = [
        Direction.UP(),
        Direction.UP(),
        Direction.LEFT(),
        Direction.RIGHT(),
        Direction.RIGHT(),
        Direction.DOWN(),
    ]

    assert _points_to_directions(h1, p1) == d1

    h2 = Point(1, 1)
    p2 = [Point(1, 2), Point(2, 2), Point(2, 1)]
    d2 = [Direction.UP(), Direction.RIGHT(), Direction.DOWN()]

    assert _points_to_directions(h2, p2) == d2

    h3 = Point(1, 1)
    p3 = [Point(2, 2)]
    with pytest.raises(ValueError):
        _points_to_directions(h3, p3)

    h4 = Point(1, 1)
    p4 = [Point(1, 1)]
    with pytest.raises(ValueError):
        _points_to_directions(h4, p4)

    h5 = Point(5, 2)
    p5 = [Point(5, 2), Point(1, 9)]
    with pytest.raises(ValueError):
        _points_to_directions(h5, p5)

    h6 = Point(7, 2)
    p6 = []
    d6 = []

    assert _points_to_directions(h6, p6) == d6


def test_directions_to_points():
    h1 = Point(6, 4)
    d1 = [Direction.RIGHT(), Direction.RIGHT(), Direction.DOWN(), Direction.UP(), Direction.UP()]
    p1 = [Point(7, 4), Point(8, 4), Point(8, 3), Point(8, 4), Point(8, 5)]

    assert _directions_to_points(h1, d1) == p1

    h2 = Point(11, 8)
    d2 = [Direction.LEFT(), Direction.DOWN(), Direction.LEFT(), Direction.UP(), Direction.RIGHT()]
    p2 = [Point(10, 8), Point(10, 7), Point(9, 7), Point(9, 8), Point(10, 8)]

    assert _directions_to_points(h2, d2) == p2
