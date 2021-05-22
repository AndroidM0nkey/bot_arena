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
    GameScore,
)
from bot_arena_server.game_config import GameConfig

import pytest
from bot_arena_proto.data import Direction, Point, SnakeState, FieldState, Object, FoodRespawnBehavior


def make_default_config(**kwargs) -> GameConfig:
    params = dict(
        snake_len = 5,
        num_food_items = 5,
        respawn_food = FoodRespawnBehavior.YES(),
        max_turns = None,
    )

    params.update(kwargs)
    return GameConfig(**params)


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

        config = make_default_config(field_width=width, field_height=height)
        field = Field(
            config = config,
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

        config = make_default_config(field_width=width, field_height=height)
        field = Field(
            config = config,
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

        config = make_default_config(field_width=width, field_height=height)
        field = Field(
            config = config,
            snakes = snakes,
            objects = objects,
        )

        with pytest.raises(NoSuchSnakeError):
            field.move_snake('E', Direction.RIGHT())

        def check(field, cell_pattern, desired_state, min_num_respawned):
            actual_state = field.get_state()
            assert actual_state.snakes == desired_state.snakes

            # XXX: food respawning is accounted for here.
            assert equal_modulo_respawn(
                set(x[0] for x in actual_state.objects),
                set(x[0] for x in desired_state.objects),
                min_num_respawned = min_num_respawned,
            )
            for yc, row in enumerate(cell_pattern):
                y = height - yc - 1
                for x, cell_state in enumerate(row):
                    cell = Point(x, y)
                    if cell_state == '.':
                        assert field.is_cell_passable(cell)
                        # TODO: accomodate object respawning in this test.
                        #assert field.is_cell_completely_free(cell)
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
        check(field, cell_pattern, desired_state, 0)

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
        check(field, cell_pattern, desired_state, 0)

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
        check(field, cell_pattern, desired_state, 1)

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
        check(field, cell_pattern, desired_state, 1)

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
        check(field, cell_pattern, desired_state, 2)

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
        check(field, cell_pattern, desired_state, 2)

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
        check(field, cell_pattern, desired_state, 2)

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
        check(field, cell_pattern, desired_state, 2)

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
        check(field, cell_pattern, desired_state, 2)

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

        config = make_default_config(field_width=width, field_height=height)
        field = Field(
            config = config,
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

        config = make_default_config(field_width=width, field_height=height)
        field = Field(
            config = config,
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
            config = config,
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

        config = make_default_config(field_width=width, field_height=height)
        field = Field(
            config = config,
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

    @staticmethod
    def test_score():
        snake_a = _Snake(head=Point(2, 4), tail=[Direction.LEFT()])
        snake_b = _Snake(head=Point(7, 3), tail=[Direction.DOWN(), Direction.DOWN()])

        objects = [
            (Point(3, 4), Object.FOOD()),
        ]

        config = make_default_config(field_width=10, field_height=10)
        field = Field(config=config, snakes={'A': snake_a}, objects=objects)

        score1 = field.get_score()
        score2 = field.get_score()
        assert score1 is not score2
        assert score1.score is not score2.score
        score1.update('A', 999)
        assert score1 != score2

        field.add_snake('B', snake_b)
        assert snake_a.score == 0
        assert snake_b.score == 0
        assert field.get_score() == GameScore({'A': 0, 'B': 0})

        field.move_snake('B', Direction.UP())
        assert snake_a.score == 0
        assert snake_b.score == 0
        assert field.get_score() == GameScore({'A': 0, 'B': 0})

        field.move_snake('B', Direction.UP())
        assert snake_a.score == 0
        assert snake_b.score == 0
        assert field.get_score() == GameScore({'A': 0, 'B': 0})

        field.move_snake('A', Direction.RIGHT())
        assert snake_a.head == Point(3, 4)
        assert snake_a.score == 1
        assert snake_b.score == 0
        assert field.get_score() == GameScore({'A': 1, 'B': 0})

        assert field.count_alive_players() == 2
        field.move_snake('A', Direction.LEFT())
        assert snake_a.score == 1
        assert snake_b.score == 0
        assert field.get_score() == GameScore({'A': 1, 'B': 0})
        assert field.count_alive_players() == 1

    @staticmethod
    def test_food_respawn_behavior():
        config = make_default_config(
            field_width = 20,
            field_height = 20,
            respawn_food = FoodRespawnBehavior.NO(),
        )
        field = Field(
            snakes = {'a': _Snake(head=Point(4, 4), tail=[Direction.LEFT()])},
            objects = [(Point(5, 4), Object.FOOD())],
            config = config,
        )
        field.move_snake('a', Direction.RIGHT())
        assert len(field._objects) == 0

        config = make_default_config(
            field_width = 20,
            field_height = 20,
            respawn_food = FoodRespawnBehavior.YES(),
        )
        field = Field(
            snakes = {'a': _Snake(head=Point(4, 4), tail=[Direction.LEFT()])},
            objects = [(Point(5, 4), Object.FOOD())],
            config = config,
        )
        field.move_snake('a', Direction.RIGHT())
        assert len(field._objects) == 1

        config = make_default_config(
            field_width = 20,
            field_height = 20,
            respawn_food = FoodRespawnBehavior.RANDOM(0.0),
        )
        field = Field(
            snakes = {'a': _Snake(head=Point(4, 4), tail=[Direction.LEFT()])},
            objects = [(Point(5, 4), Object.FOOD())],
            config = config,
        )
        field.move_snake('a', Direction.RIGHT())
        assert len(field._objects) == 0
        field.move_snake('a', Direction.UP())
        assert len(field._objects) == 0

        config = make_default_config(
            field_width = 20,
            field_height = 20,
            respawn_food = FoodRespawnBehavior.RANDOM(1.0),
        )
        field = Field(
            snakes = {'a': _Snake(head=Point(4, 4), tail=[Direction.LEFT()])},
            objects = [(Point(5, 5), Object.FOOD())],
            config = config,
        )
        field.move_snake('a', Direction.RIGHT())
        assert len(field._objects) == 2

        field.move_snake('a', Direction.UP())
        assert len(field._objects) == 2


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

        config = make_default_config(field_width=width, field_height=height)
        field = Field(
            config = config,
            snakes = snakes,
            objects = objects,
        )

        game = Game(list(snakes.keys()), config)
        game._field = field

        assert game.take_turn('A', Action.MOVE(Direction.LEFT())) == MoveResult.OK()
        assert fs_equal_modulo_respawn(field.get_state(), FieldState(
            snakes = {
                'A': SnakeState(Point(7, 3), [Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT()]),
                'B': SnakeState(Point(0, 0), []),
            },
            objects = [(Point(6, 3), Object.FOOD())],
        ), 0)

        assert game.take_turn('A', Action.MOVE(Direction.LEFT())) == MoveResult.OK()
        assert fs_equal_modulo_respawn(field.get_state(), FieldState(
            snakes = {
                'A': SnakeState(
                    Point(6, 3),
                    [Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT()]
                ),
                'B': SnakeState(Point(0, 0), []),
            },
            objects = [],
        ), 1)

        assert game.take_turn('B', Action.MOVE(Direction.DOWN())) == MoveResult.CRASH()
        assert fs_equal_modulo_respawn(field.get_state(), FieldState(
            snakes = {
                'A': SnakeState(
                    Point(6, 3),
                    [Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT()]
                ),
            },
            objects = [],
        ), 1)

        with pytest.raises(NoSuchSnakeError):
            game.take_turn('C', Action.MOVE(Direction.DOWN()))

        with pytest.raises(NoSuchSnakeError):
            game.take_turn('B', Action.MOVE(Direction.DOWN()))

    @staticmethod
    def test_snake_names():
        for names in [['A', 'B', 'C', 'foo', 'Barr'], [], ['0']]:
            config = make_default_config(field_width=10, field_height=10)
            game = Game(names, config)
            assert set(game.snake_names()) == set(names)

    @staticmethod
    def test_info():
        config = make_default_config(field_width=326, field_height=16)
        game = Game(['A', 'B'], config)
        assert game.info() == GameInfo(field_width=326, field_height=16)


def _points():
    return (
        Point(1, 1),
        Point(2, 2),
        Point(3, 3),
        Point(4, 4),    # <--- D1   This coincidence is intentional
        Point(4, 4),    # <--- D2
        Point(5, 5),
        Point(6, 6),
        Point(7, 7),
    )


class TestChangeInFreeCells:
    @staticmethod
    def test_init():
        A, B, C, D1, D2, E, F, G = _points()

        cf = ChangeInFreeCells([A, B, C], [E, F])
        assert cf._new_free == {A, B, C}
        assert cf._new_occupied == {E, F}

        cf = ChangeInFreeCells([A, B, C], [C, E, F])
        assert cf._new_free == {A, B}
        assert cf._new_occupied == {E, F}

        cf = ChangeInFreeCells([A, B], [B])
        assert cf._new_free == {A}
        assert cf._new_occupied == set()

        cf = ChangeInFreeCells([A], [A, B])
        assert cf._new_free == set()
        assert cf._new_occupied == {B}

        cf = ChangeInFreeCells([A, A], [])
        assert cf._new_free == {A}
        assert cf._new_occupied == set()

        cf = ChangeInFreeCells([], [D1, D2])
        assert cf._new_free == set()
        assert cf._new_occupied == {D1} == {D2}

        cf = ChangeInFreeCells([], [])
        assert cf._new_free == set()
        assert cf._new_occupied == set()

        cf = ChangeInFreeCells([A, D1, F], [D2, E, F])
        assert cf._new_free == {A}
        assert cf._new_occupied == {E}

    @staticmethod
    def test_eq():
        A, B, C, D1, D2, E, F, G = _points()

        assert ChangeInFreeCells([A], [B, C]) == ChangeInFreeCells([A], [B, C])
        assert ChangeInFreeCells([], [B, C]) == ChangeInFreeCells([A], [A, B, C])
        assert ChangeInFreeCells([A], [B, C]) != ChangeInFreeCells([], [B, C])
        assert ChangeInFreeCells([], []) == ChangeInFreeCells([], [])
        assert ChangeInFreeCells([D1], []) == ChangeInFreeCells([D2], [])
        assert ChangeInFreeCells([D1], [D2]) == ChangeInFreeCells([], [])
        assert ChangeInFreeCells([A], [B]) != ChangeInFreeCells([B], [A])
        assert ChangeInFreeCells([A], []) != ChangeInFreeCells([], [A])
        assert ChangeInFreeCells([A, B, C], [E, F, G]) == ChangeInFreeCells([A, B, C, D1], [D2, E, F, G])

    @staticmethod
    def test_add_new_free():
        A, B, C, D1, D2, E, F, G = _points()

        cf = ChangeInFreeCells([A, B], [E, F, G])
        cf.add_new_free(C)
        assert cf == ChangeInFreeCells([A, B, C], [E, F, G])

        cf = ChangeInFreeCells([A, B], [E, F, G])
        cf.add_new_free(E)
        assert cf == ChangeInFreeCells([A, B, E], [E, F, G]) == ChangeInFreeCells([A, B], [F, G])
        cf.add_new_free(E)
        assert cf == ChangeInFreeCells([A, B, E], [F, G]) != ChangeInFreeCells([A, B], [F, G])
        cf.add_new_free(E)
        assert cf == ChangeInFreeCells([A, B, E], [F, G])

        cf = ChangeInFreeCells([], [A, B, C, D1, E, F, G])
        cf.add_new_free(A)
        assert cf._new_free == set()
        assert cf._new_occupied == {B, C, D1, E, F, G}

        cf = ChangeInFreeCells([A, B, C, D1, E, F, G], [])
        cf.add_new_free(A)
        assert cf._new_free == {A, B, C, D1, E, F, G}
        assert cf._new_occupied == set()

    @staticmethod
    def test_add_new_occupied():
        A, B, C, D1, D2, E, F, G = _points()

        cf = ChangeInFreeCells([A, B], [E, F, G])
        cf.add_new_occupied(C)
        assert cf == ChangeInFreeCells([A, B], [C, E, F, G])

        cf = ChangeInFreeCells([A, B, E], [F, G])
        cf.add_new_occupied(E)
        assert cf == ChangeInFreeCells([A, B, E], [E, F, G]) == ChangeInFreeCells([A, B], [F, G])
        cf.add_new_occupied(E)
        assert cf == ChangeInFreeCells([A, B], [E, F, G]) != ChangeInFreeCells([A, B], [F, G])
        cf.add_new_occupied(E)
        assert cf == ChangeInFreeCells([A, B], [E, F, G])

        cf = ChangeInFreeCells([], [A, B, C, D1, E, F, G])
        cf.add_new_occupied(A)
        assert cf._new_free == set()
        assert cf._new_occupied == {A, B, C, D1, E, F, G}

        cf = ChangeInFreeCells([A, B, C, D1, E, F, G], [])
        cf.add_new_occupied(A)
        assert cf._new_free == {B, C, D1, E, F, G}
        assert cf._new_occupied == set()

    @staticmethod
    def test_accessors_work():
        A, B, C, D1, D2, E, F, G = _points()

        cf = ChangeInFreeCells([A, B], [C, A, D1, D2, F])
        assert cf.new_free() == {B} == cf._new_free
        assert cf.new_occupied() == {C, D1, F} == cf._new_occupied

        cf = ChangeInFreeCells([A, B], [A, B])
        assert cf.new_free() == set() == cf._new_free
        assert cf.new_occupied() == set() == cf._new_occupied

        cf = ChangeInFreeCells([], [])
        assert cf.new_free() == set() == cf._new_free
        assert cf.new_occupied() == set() == cf._new_occupied

    @staticmethod
    def test_accessors_copy():
        A, B, C, D1, D2, E, F, G = _points()

        cf = ChangeInFreeCells([A], [F])
        new_free = cf.new_free()
        new_occupied = cf.new_occupied()
        assert new_free is not cf._new_free
        assert new_occupied is not cf._new_occupied

        new_free.add(B)
        new_occupied.add(E)
        assert cf._new_free == {A} != new_free == {A, B}
        assert cf._new_occupied == {F} != new_occupied == {E, F}


class TestScore:
    @staticmethod
    def test_get_winners():
        assert GameScore({}).get_winners(lambda _: True) == []
        assert GameScore({'A': 5, 'B': 7, 'C': 3, 'D': 5}).get_winners(lambda _: True) == ['B']
        assert set(GameScore({'A': 5, 'B': 7, 'C': 3, 'D': 7}).get_winners(lambda _: True)) == {'B', 'D'}
        assert set(GameScore.from_snake_names(['a', 'b', 'c']).get_winners(lambda _: True)) == {'a', 'b', 'c'}
        assert set(
            GameScore
                .from_snake_names({'a': 3, 'b': 3, 'c': 5})
                .get_winners(lambda name: name < 'c')
        ) == {'a', 'b'}


def equal_modulo_respawn(set1, set2, min_num_respawned):
    return len(set1) >= len(set2) + min_num_respawned and all(x in set1 for x in set2)

def fs_equal_modulo_respawn(fs1, fs2, min_num_respawned):
    return fs1.snakes == fs2.snakes and equal_modulo_respawn(fs1.objects, fs2.objects, min_num_respawned)
