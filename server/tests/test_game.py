import copy

from bot_arena_server.game import (
    _Snake,
    _points_to_directions,
    _directions_to_points,
    Field,
    NoSuchSnakeError,
    MoveResult,
    ChangeInFreeCells,
    Game,
    Action,
    GameInfo,
)

import pytest
from bot_arena_proto.data import Direction, Point, SnakeState, FieldState, Object


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

        assert snake.grow(Direction.UP()) == ChangeInFreeCells([], [Point(2, 5)])
        assert snake.get_state() == SnakeState(
            head = Point(2, 5),
            tail = [Direction.DOWN()],
        )

        assert snake.grow(Direction.UP()) == ChangeInFreeCells([], [Point(2, 6)])
        assert snake.get_state() == SnakeState(
            head = Point(2, 6),
            tail = [Direction.DOWN(), Direction.DOWN()],
        )

        assert snake.grow(Direction.LEFT()) == ChangeInFreeCells([], [Point(1, 6)])
        assert snake.get_state() == SnakeState(
            head = Point(1, 6),
            tail = [Direction.RIGHT(), Direction.DOWN(), Direction.DOWN()],
        )

        assert snake.grow(Direction.DOWN()) == ChangeInFreeCells([], [Point(1, 5)])
        assert snake.get_state() == SnakeState(
            head = Point(1, 5),
            tail = [Direction.UP(), Direction.RIGHT(), Direction.DOWN(), Direction.DOWN()],
        )

        assert snake.grow(Direction.RIGHT()) == ChangeInFreeCells([], [Point(2, 5)])
        assert snake.get_state() == SnakeState(
            head = Point(2, 5),
            tail = [Direction.LEFT(), Direction.UP(), Direction.RIGHT(), Direction.DOWN(), Direction.DOWN()],
        )

    @staticmethod
    def test_move():
        snake = _Snake(head=Point(2, 4), tail=[Direction.RIGHT(), Direction.DOWN(), Direction.LEFT()])

        assert snake.move(Direction.UP()) == ChangeInFreeCells([Point(2, 3)], [Point(2, 5)])
        assert snake.get_state() == SnakeState(
            head = Point(2, 5),
            tail = [Direction.DOWN(), Direction.RIGHT(), Direction.DOWN()],
        )

        assert snake.move(Direction.UP()) == ChangeInFreeCells([Point(3, 3)], [Point(2, 6)])
        assert snake.get_state() == SnakeState(
            head = Point(2, 6),
            tail = [Direction.DOWN(), Direction.DOWN(), Direction.RIGHT()],
        )

        assert snake.move(Direction.LEFT()) == ChangeInFreeCells([Point(3, 4)], [Point(1, 6)])
        assert snake.get_state() == SnakeState(
            head = Point(1, 6),
            tail = [Direction.RIGHT(), Direction.DOWN(), Direction.DOWN()],
        )

        assert snake.move(Direction.DOWN()) == ChangeInFreeCells([Point(2, 4)], [Point(1, 5)])
        assert snake.get_state() == SnakeState(
            head = Point(1, 5),
            tail = [Direction.UP(), Direction.RIGHT(), Direction.DOWN()],
        )

        assert snake.move(Direction.RIGHT()) == ChangeInFreeCells([], [])
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


class TestField:
    @staticmethod
    def test_get_state():
        bob = _Snake(head=Point(11, 63), tail=[Direction.LEFT(), Direction.UP()])
        mike = _Snake(head=Point(14, 9), tail=[Direction.DOWN()])
        width = 42
        height = 87
        snakes = {'Bob': bob, 'Mike': mike}
        objects = [(Point(15, 8), Object.FOOD()), (Point(11, 11), Object.FOOD())]

        field = Field(
            width = width,
            height = height,
            snakes = snakes,
            objects = objects,
        )

        state = field.get_state()
        assert set(state.objects) == set(objects)
        assert state.snakes == {name: snake.get_state() for name, snake in snakes.items()}

    @staticmethod
    def test_random_free_cell():
        width = 5
        height = 6
        n = 5000
        snakes = {
            'A': _Snake(head=Point(2, 2), tail=[Direction.UP(), Direction.RIGHT()]),
            'B': _Snake(head=Point(4, 4), tail=[]),
        }
        objects = [(Point(0, 0), Object.FOOD()), (Point(4, 2), Object.FOOD())]

        field = Field(
            width = width,
            height = height,
            snakes = snakes,
            objects = objects,
        )

        occupied_cells = {Point(0, 0), Point(4, 2), Point(2, 2), Point(2, 3), Point(3, 3), Point(4, 4)}

        obtained_cells = set()
        for i in range(n):
            cell = field.random_free_cell()
            assert 0 <= cell.x < width
            assert 0 <= cell.y < height
            assert field.is_cell_completely_free(cell)
            assert cell not in occupied_cells
            obtained_cells.add(cell)

        # P(false alarm) < 10^(-90)
        assert len(obtained_cells) == width * height - len(occupied_cells)

    @staticmethod
    def test_move_snake():
        width = 10
        height = 6
        snakes = {
            'A': _Snake(head=Point(4, 2), tail=[Direction.DOWN()]),
            'B': _Snake(head=Point(9, 5), tail=[Direction.LEFT(), Direction.LEFT()]),
            'C': _Snake(head=Point(0, 0), tail=[]),
            'D': _Snake(head=Point(0, 1), tail=[]),
        }
        objects = [(Point(4, 4), Object.FOOD()), (Point(9, 4), Object.FOOD())]

        field = Field(
            width = width,
            height = height,
            snakes = snakes,
            objects = objects,
        )

        with pytest.raises(NoSuchSnakeError):
            field.move_snake('E', Direction.RIGHT())

        def check(field, cell_pattern, desired_state):
            actual_state = field.get_state()
            assert actual_state.snakes == desired_state.snakes
            assert set(x[0] for x in actual_state.objects) == set(x[0] for x in desired_state.objects)
            for yc, row in enumerate(cell_pattern):
                y = height - yc - 1
                for x, cell_state in enumerate(row):
                    cell = Point(x, y)
                    if cell_state == '.':
                        assert field.is_cell_passable(cell)
                        assert field.is_cell_completely_free(cell)
                    elif cell_state == '=':
                        assert field.is_cell_passable(cell)
                        assert not field.is_cell_completely_free(cell)
                    elif cell_state == '#':
                        assert not field.is_cell_passable(cell)
                        assert not field.is_cell_completely_free(cell)
                    else:
                        raise

        cell_pattern = [
            '.......###',
            '....=....=',
            '..........',
            '....#.....',
            '#...#.....',
            '#.........',
        ]
        desired_state = FieldState(
            snakes = {
                'A': SnakeState(head=Point(4, 2), tail=[Direction.DOWN()]),
                'B': SnakeState(head=Point(9, 5), tail=[Direction.LEFT(), Direction.LEFT()]),
                'C': SnakeState(head=Point(0, 0), tail=[]),
                'D': SnakeState(head=Point(0, 1), tail=[]),
            },
            objects = [(Point(4, 4), Object.FOOD()), (Point(9, 4), Object.FOOD())],
        )
        check(field, cell_pattern, desired_state)

        assert field.move_snake('A', Direction.UP()) == MoveResult.OK()
        cell_pattern = [
            '.......###',
            '....=....=',
            '....#.....',
            '....#.....',
            '#.........',
            '#.........',
        ]
        desired_state = FieldState(
            snakes = {
                'A': SnakeState(head=Point(4, 3), tail=[Direction.DOWN()]),
                'B': SnakeState(head=Point(9, 5), tail=[Direction.LEFT(), Direction.LEFT()]),
                'C': SnakeState(head=Point(0, 0), tail=[]),
                'D': SnakeState(head=Point(0, 1), tail=[]),
            },
            objects = [(Point(4, 4), Object.FOOD()), (Point(9, 4), Object.FOOD())],
        )
        check(field, cell_pattern, desired_state)

        assert field.move_snake('B', Direction.DOWN()) == MoveResult.OK()
        cell_pattern = [
            '.......###',
            '....=....#',
            '....#.....',
            '....#.....',
            '#.........',
            '#.........',
        ]
        desired_state = FieldState(
            snakes = {
                'A': SnakeState(head=Point(4, 3), tail=[Direction.DOWN()]),
                'B': SnakeState(head=Point(9, 4), tail=[Direction.UP(), Direction.LEFT(), Direction.LEFT()]),
                'C': SnakeState(head=Point(0, 0), tail=[]),
                'D': SnakeState(head=Point(0, 1), tail=[]),
            },
            objects = [(Point(4, 4), Object.FOOD())],
        )
        check(field, cell_pattern, desired_state)

        assert field.move_snake('B', Direction.UP()) == MoveResult.CRASH()
        cell_pattern = [
            '..........',
            '....=.....',
            '....#.....',
            '....#.....',
            '#.........',
            '#.........',
        ]
        desired_state = FieldState(
            snakes = {
                'A': SnakeState(head=Point(4, 3), tail=[Direction.DOWN()]),
                'C': SnakeState(head=Point(0, 0), tail=[]),
                'D': SnakeState(head=Point(0, 1), tail=[]),
            },
            objects = [(Point(4, 4), Object.FOOD())],
        )
        check(field, cell_pattern, desired_state)

        with pytest.raises(NoSuchSnakeError):
            field.move_snake('B', Direction.LEFT())

        assert field.move_snake('A', Direction.UP()) == MoveResult.OK()
        cell_pattern = [
            '..........',
            '....#.....',
            '....#.....',
            '....#.....',
            '#.........',
            '#.........',
        ]
        desired_state = FieldState(
            snakes = {
                'A': SnakeState(head=Point(4, 4), tail=[Direction.DOWN(), Direction.DOWN()]),
                'C': SnakeState(head=Point(0, 0), tail=[]),
                'D': SnakeState(head=Point(0, 1), tail=[]),
            },
            objects = [],
        )
        check(field, cell_pattern, desired_state)

        assert field.move_snake('C', Direction.UP()) == MoveResult.CRASH()
        cell_pattern = [
            '..........',
            '....#.....',
            '....#.....',
            '....#.....',
            '#.........',
            '..........',
        ]
        desired_state = FieldState(
            snakes = {
                'A': SnakeState(head=Point(4, 4), tail=[Direction.DOWN(), Direction.DOWN()]),
                'D': SnakeState(head=Point(0, 1), tail=[]),
            },
            objects = [],
        )
        check(field, cell_pattern, desired_state)

        assert field.move_snake('D', Direction.DOWN()) == MoveResult.OK()
        cell_pattern = [
            '..........',
            '....#.....',
            '....#.....',
            '....#.....',
            '..........',
            '#.........',
        ]
        desired_state = FieldState(
            snakes = {
                'A': SnakeState(head=Point(4, 4), tail=[Direction.DOWN(), Direction.DOWN()]),
                'D': SnakeState(head=Point(0, 0), tail=[]),
            },
            objects = [],
        )
        check(field, cell_pattern, desired_state)

        assert field.move_snake('D', Direction.DOWN()) == MoveResult.CRASH()
        cell_pattern = [
            '..........',
            '....#.....',
            '....#.....',
            '....#.....',
            '..........',
            '..........',
        ]
        desired_state = FieldState(
            snakes = {
                'A': SnakeState(head=Point(4, 4), tail=[Direction.DOWN(), Direction.DOWN()]),
            },
            objects = [],
        )
        check(field, cell_pattern, desired_state)

        assert field.move_snake('A', Direction.UP()) == MoveResult.OK()
        assert field.move_snake('A', Direction.UP()) == MoveResult.CRASH()
        cell_pattern = [
            '..........',
            '..........',
            '..........',
            '..........',
            '..........',
            '..........',
        ]
        desired_state = FieldState(
            snakes = {},
            objects = [],
        )
        check(field, cell_pattern, desired_state)

    @staticmethod
    def test_is_cell_passable():
        width = 5
        height = 6
        n = 5000
        snakes = {
            'A': _Snake(head=Point(2, 2), tail=[Direction.UP(), Direction.RIGHT()]),
            'B': _Snake(head=Point(4, 4), tail=[]),
        }
        objects = [(Point(0, 0), Object.FOOD()), (Point(4, 2), Object.FOOD())]

        field = Field(
            width = width,
            height = height,
            snakes = snakes,
            objects = objects,
        )

        impassable_cells = {Point(2, 2), Point(2, 3), Point(3, 3), Point(4, 4)}

        for x in range(width):
            for y in range(height):
                cell = Point(x, y)
                assert field.is_cell_passable(cell) == (cell not in impassable_cells)

        assert not field.is_cell_passable(Point(5, 6))
        assert not field.is_cell_passable(Point(5, 5))
        assert not field.is_cell_passable(Point(4, 6))
        assert not field.is_cell_passable(Point(0, -1))
        assert not field.is_cell_passable(Point(-1, 0))
        assert not field.is_cell_passable(Point(-26, 1264))
        assert field.is_cell_passable(Point(0, 0))

    @staticmethod
    def test_is_cell_completely_free():
        width = 5
        height = 6
        snakes = {
            'A': _Snake(head=Point(2, 2), tail=[Direction.UP(), Direction.RIGHT()]),
            'B': _Snake(head=Point(4, 4), tail=[]),
        }
        objects = [(Point(0, 0), Object.FOOD()), (Point(4, 2), Object.FOOD())]

        field = Field(
            width = width,
            height = height,
            snakes = snakes,
            objects = objects,
        )

        occupied_cells = {Point(0, 0), Point(4, 2), Point(2, 2), Point(2, 3), Point(3, 3), Point(4, 4)}

        for x in range(width):
            for y in range(height):
                cell = Point(x, y)
                assert field.is_cell_completely_free(cell) == (cell not in occupied_cells)

        assert not field.is_cell_completely_free(Point(5, 6))
        assert not field.is_cell_completely_free(Point(5, 5))
        assert not field.is_cell_completely_free(Point(4, 6))
        assert not field.is_cell_completely_free(Point(0, -1))
        assert not field.is_cell_completely_free(Point(-1, 0))
        assert not field.is_cell_completely_free(Point(-26, 1264))
        assert field.is_cell_completely_free(Point(4, 5))

        width = 5
        height = 6
        snakes = {
            'A': _Snake(head=Point(0, 0), tail=[Direction.RIGHT()] * (width - 1)),
        }
        free_cells = {Point(4, 2), Point(3, 3), Point(0, 5)}
        objects = [
            (Point(x, y), Object.FOOD())
            for x in range(width)
            for y in range(1, height)
            if Point(x, y) not in free_cells
        ]

        field = Field(
            width = width,
            height = height,
            snakes = snakes,
            objects = objects,
        )

        for x in range(width):
            for y in range(height):
                cell = Point(x, y)
                assert field.is_cell_completely_free(cell) == (cell in free_cells)

    @staticmethod
    def test_place_object_randomly():
        width = 5
        height = 6
        n = 200
        snakes = {
            'A': _Snake(head=Point(0, 0), tail=[Direction.RIGHT()] * (width - 1)),
        }
        free_cells = {Point(4, 2), Point(3, 3), Point(0, 5)}
        objects = [
            (Point(x, y), Object.FOOD())
            for x in range(width)
            for y in range(1, height)
            if Point(x, y) not in free_cells
        ]

        field = Field(
            width = width,
            height = height,
            snakes = snakes,
            objects = objects,
        )

        initial_set = field._objects.keys()

        for i in range(n):
            field_copy = copy.deepcopy(field)
            field_copy.place_object_randomly(Object.FOOD())
            set_diff = set(field_copy._objects.keys()) - initial_set
            assert len(set_diff) == 1
            [new_cell] = set_diff
            assert new_cell in free_cells
            assert field.is_cell_completely_free(new_cell)
            assert not field_copy.is_cell_completely_free(new_cell)


class TestGame:
    @staticmethod
    def test_take_turn():
        width = 20
        height = 10
        snakes = {
            'A': _Snake(Point(8, 3), [Direction.RIGHT(), Direction.RIGHT(), Direction.UP()]),
            'B': _Snake(Point(0, 0), []),
        }
        objects = [(Point(6, 3), Object.FOOD())]

        field = Field(
            width = width,
            height = height,
            snakes = snakes,
            objects = objects,
        )

        game = Game(width, height, list(snakes.keys()))
        game._field = field

        assert game.take_turn('A', Action.MOVE(Direction.LEFT())) == MoveResult.OK()
        assert field.get_state() == FieldState(
            snakes = {
                'A': SnakeState(Point(7, 3), [Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT()]),
                'B': SnakeState(Point(0, 0), []),
            },
            objects = [(Point(6, 3), Object.FOOD())],
        )

        assert game.take_turn('A', Action.MOVE(Direction.LEFT())) == MoveResult.OK()
        assert field.get_state() == FieldState(
            snakes = {
                'A': SnakeState(
                    Point(6, 3),
                    [Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT()]
                ),
                'B': SnakeState(Point(0, 0), []),
            },
            objects = [],
        )

        assert game.take_turn('B', Action.MOVE(Direction.DOWN())) == MoveResult.CRASH()
        assert field.get_state() == FieldState(
            snakes = {
                'A': SnakeState(
                    Point(6, 3),
                    [Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT()]
                ),
            },
            objects = [],
        )

        with pytest.raises(NoSuchSnakeError):
            game.take_turn('C', Action.MOVE(Direction.DOWN()))

        with pytest.raises(NoSuchSnakeError):
            game.take_turn('B', Action.MOVE(Direction.DOWN()))

    @staticmethod
    def test_snake_names():
        for names in [['A', 'B', 'C', 'foo', 'Barr'], [], ['0']]:
            game = Game(10, 10, names)
            assert set(game.snake_names()) == set(names)

    @staticmethod
    def test_info():
        game = Game(326, 16, ['A', 'B'])
        assert game.info() == GameInfo(field_width=326, field_height=16)
