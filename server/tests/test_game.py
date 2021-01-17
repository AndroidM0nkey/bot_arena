from bot_arena_server.game import _Snake

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
