from bot_arena_server.game_config import GameConfig

import random
from copy import copy
from dataclasses import dataclass
from typing import List, Callable, Tuple, Dict, Set, Generator, Optional, Iterable

from adt import adt, Case
from bot_arena_proto.data import SnakeState, Direction, Point, Object, FieldState, Action
from bot_arena_proto.session import GameInfo


__all__ = [
    'Field',
    'Game',
    'GameScore',
    'IllegalAction',
    'InvalidMoveError',
    'MoveResult',
    'NoSuchSnakeError',
]


class ChangeInFreeCells:
    def __init__(self, new_free: Iterable[Point], new_occupied: Iterable[Point]):
        new_free = set(new_free)
        new_occupied = set(new_occupied)
        self._new_free = new_free - new_occupied
        self._new_occupied = new_occupied - new_free

    def __eq__(self, other: object) -> bool:
        # I hate Python's type system so much.
        if not isinstance(other, ChangeInFreeCells):
            return NotImplemented
        return (self._new_free, self._new_occupied) == (other._new_free, other._new_occupied)

    def __repr__(self) -> str:
        return f'ChangeInFreeCells(new_free={self._new_free!r}, new_occupied={self._new_occupied!r})'

    def add_new_free(self, point: Point):
        if point in self._new_occupied:
            self._new_occupied.remove(point)
        else:
            self._new_free.add(point)

    def add_new_occupied(self, point: Point):
        if point in self._new_free:
            self._new_free.remove(point)
        else:
            self._new_occupied.add(point)

    def new_free(self) -> Set[Point]:
        return copy(self._new_free)

    def new_occupied(self) -> Set[Point]:
        return copy(self._new_occupied)


class IllegalAction(Exception):
    pass


class InvalidMoveError(IllegalAction):
    def __str__(self) -> str:
        return 'Invalid move'


class NoSuchSnakeError(IllegalAction):
    def __init__(self, snake_name: str) -> None:
        self._snake_name = snake_name

    def __str__(self) -> str:
        return f'No such snake: {self._snake_name!r}'


@adt
class MoveResult:
    OK: Case
    CRASH: Case


def _generate_snake(field: 'Field', length: int) -> '_Snake':
    while True:
        maybe_snake = _try_generate_snake(field, length)
        if maybe_snake is not None:
            return maybe_snake


def _try_generate_snake(field: 'Field', length: int) -> Optional['_Snake']:
    tail = []
    head = field.random_free_cell()
    snake_cells = {head}

    for _ in range(length - 1):
        next_cell_candidates = []
        for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            candidate = Point(head.x + dx, head.y + dy)
            if field.is_cell_completely_free(candidate) and candidate not in snake_cells:
                next_cell_candidates.append(candidate)

        if len(next_cell_candidates) == 0:
            return None

        next_cell = random.choice(next_cell_candidates)
        tail.append(head)
        head = next_cell
        snake_cells.add(next_cell)

    tail.reverse()

    # TODO: run DFS or BFS to ensure that the snake isn't locked out.
    return _Snake.from_raw_parts(head, tail)


class Game:
    def __init__(self, snake_names: List[str], config: GameConfig) -> None:
        self._config = config
        self._turns_counter = 0
        self._field = Field(
            config = config,
            snakes = {},
            objects = [],
        )

        for name in snake_names:
            snake = _generate_snake(self._field, self._config.snake_len)
            self._field.add_snake(name, snake)

        for i in range(self._config.num_food_items):
            self._field.place_object_randomly(Object.FOOD())

    def finish_turn(self) -> None:
        self._turns_counter += 1

    def get_score(self) -> 'GameScore':
        return self._field.get_score()

    @property
    def field(self) -> 'Field':
        return self._field

    def take_turn(self, name: str, action: Action) -> MoveResult:
        return action.match(
            move = lambda direction: self.field.move_snake(name, direction),
        ) # type: ignore

    def info(self) -> GameInfo:
        return GameInfo(field_width=self._field.width, field_height=self._field.height)

    def snake_names(self) -> Iterable[str]:
        return self.field._snakes.keys()

    def turn_limit_exceeded(self) -> bool:
        return (self._config.max_turns is not None) and (self._turns_counter >= self._config.max_turns)

    def is_finish_condition_satisfied(self) -> bool:
        # TODO: make the finish condition configurable.
        return self.field.count_alive_players() <= 1 or self.turn_limit_exceeded()

    def get_winners(self) -> Optional[List[str]]:
        if not self.is_finish_condition_satisfied():
            return None

        return self.get_score().get_winners(lambda name: name in self.field._snakes)

    def kill_snake_off(self, snake_name: str):
        if snake_name in set(self.snake_names()):
            self.field.kill_snake(snake_name)


@dataclass
class GameScore:
    score: Dict[str, int]

    @staticmethod
    def from_snake_names(names: Iterable[str]) -> 'GameScore':
        return GameScore(score={name: 0 for name in names})

    def update(self, name: str, new_score: int) -> None:
        self.score[name] = new_score

    def copy(self) -> 'GameScore':
        return GameScore(copy(self.score))

    def get_winners(self, candidate_checker: Callable[[str], bool]) -> List[str]:
        score_dict = {name: value for name, value in self.score.items() if candidate_checker(name)}
        if len(score_dict) == 0:
            return []

        max_score = max(value for value in score_dict.values())
        return list(name for name, value in score_dict.items() if value == max_score)


class Field:
    def __init__(
        self,
        snakes: Dict[str, '_Snake'],
        objects: List[Tuple[Point, Object]],
        config: GameConfig,
    ) -> None:
        self._config = config
        self._snakes = snakes
        self._objects: Dict[Point, Object] = dict(objects)
        self._occupied_cells: Set[Point] = set()
        self._game_score = GameScore.from_snake_names(self._snakes.keys())
        for snake in snakes.values():
            self._occupied_cells.update(snake.list_occupied_cells())

    def get_score(self) -> GameScore:
        for name, snake in self._snakes.items():
            self._game_score.update(name, snake.score)
        return self._game_score.copy()

    def random_free_cell(self) -> Point:
        while True:
            cell = self._try_random_free_cell()
            if cell is not None:
                return cell

    def _try_random_free_cell(self) -> Optional[Point]:
        x = random.randrange(0, self.width)
        y = random.randrange(0, self.height)
        point = Point(x, y)
        return point if self.is_cell_completely_free(point) else None

    def count_alive_players(self) -> int:
        return len(self._snakes)

    def kill_snake(self, name: str) -> None:
        if name not in self._snakes:
            raise NoSuchSnakeError(name)

        snake = self._snakes[name]
        self._update_occupied_cells(
            ChangeInFreeCells(new_free=snake.list_occupied_cells(), new_occupied=[])
        )

        self._snakes.pop(name)

    def move_snake(self, name: str, direction: Direction) -> MoveResult:
        if name not in self._snakes:
            raise NoSuchSnakeError(name)

        snake = self._snakes[name]

        destination = snake.head.shift(direction)
        try:
            if not self.is_cell_passable(destination):
                # The snake has crashed.
                # Free up the cells that were occupied by this snake.
                self._update_occupied_cells(
                    ChangeInFreeCells(new_free=snake.list_occupied_cells(), new_occupied=[])
                )
                # Delete it from the world.
                self._snakes.pop(name)
                # Report the death.
                return MoveResult.CRASH()

            if destination in self._objects:
                obj = self._objects[destination]
                return obj.match(
                    food = lambda: self._consume_food(snake, direction)
                ) # type: ignore

            change_in_free_cells = snake.move(direction)
            self._update_occupied_cells(change_in_free_cells)

        finally:
            self._do_object_placement_step()

        return MoveResult.OK()

    def _consume_food(self, snake: '_Snake', direction: Direction) -> MoveResult:
        self._update_occupied_cells(snake.grow(direction))
        self._objects.pop(snake.head)
        snake.change_score_by(1)

        self._maybe_respawn_food_item()

        return MoveResult.OK()

    def _maybe_respawn_food_item(self) -> None:
        self._config.respawn_food.match(
            yes = lambda: self.place_object_randomly(Object.FOOD()),
            no = lambda: None,
            random = lambda _: None,
        ) # type: ignore

    def _update_occupied_cells(self, change_in_free_cells: ChangeInFreeCells) -> None:
        for cell in change_in_free_cells.new_occupied():
            self._occupied_cells.add(cell)

        for cell in change_in_free_cells.new_free():
            self._occupied_cells.remove(cell)

    def is_cell_passable(self, cell: Point) -> bool:
        if cell not in self:
            return False

        return cell not in self._occupied_cells

    def __contains__(self, cell: Point) -> bool:
        return 0 <= cell.x < self.width and 0 <= cell.y < self.height

    def get_state(self) -> FieldState:
        return FieldState(
            snakes = {name: snake.get_state() for name, snake in self._snakes.items()},
            objects = list(self._objects.items()),
        )

    @property
    def width(self) -> int:
        return self._config.field_width

    @property
    def height(self) -> int:
        return self._config.field_height

    def place_object_randomly(self, obj: Object) -> None:
        while not self.try_place_object_randomly(obj):
            pass

    def try_place_object_randomly(self, obj: Object) -> bool:
        x = random.randrange(0, self.width)
        y = random.randrange(0, self.height)
        point = Point(x, y)
        if self.is_cell_completely_free(point):
            self._place_object_at(obj, point)
            return True
        else:
            return False

    def _do_object_placement_step(self) -> None:
        self._config.respawn_food.match(
            yes = lambda: None,     # TODO: respawn lost objects.
            no = lambda: None,
            random = self._do_probability_object_placement_step,
        ) # type: ignore

    def _do_probability_object_placement_step(self, probability: float) -> None:
        random_value = random.random()
        if random_value >= probability:
            return

        self.place_object_randomly(Object.FOOD())

    def is_cell_completely_free(self, cell: Point) -> bool:
        return (cell in self) and (cell not in self._occupied_cells) and (cell not in self._objects)

    def _place_object_at(self, obj: Object, point: Point) -> None:
        self._objects[point] = obj

    def add_snake(self, snake_name: str, snake: '_Snake') -> None:
        if snake_name in self._snakes:
            raise KeyError(f'Snake {snake_name!r} is already present on the game field')
        self._snakes[snake_name] = snake
        self._update_occupied_cells(
            ChangeInFreeCells(new_free=[], new_occupied=snake.list_occupied_cells())
        )


def _directions_to_points(head: Point, tail: List[Direction]) -> List[Point]:
    result: List[Point] = []
    position = head
    for direction in tail:
        position = position.shift(direction)
        result.append(position)
    return result


def _points_to_directions(head: Point, tail: List[Point]) -> List[Direction]:
    def inner() -> Generator[Direction, None, None]:
        last_point = head
        for point in tail:
            dx = point.x - last_point.x
            dy = point.y - last_point.y

            if dx == 1 and dy == 0:
                yield Direction.RIGHT()
            elif dx == -1 and dy == 0:
                yield Direction.LEFT()
            elif dx == 0 and dy == 1:
                yield Direction.UP()
            elif dx == 0 and dy == -1:
                yield Direction.DOWN()
            else:
                raise ValueError(f'Invalid tail: {tail!r}')

            last_point = point

    return list(inner())


class _Snake:
    def __init__(self, head: Point, tail: List[Direction]) -> None:
        self._head = head
        self._tail = _directions_to_points(head, tail)
        self._score = 0

    @property
    def score(self) -> int:
        return self._score

    def change_score_by(self, score_delta: int) -> None:
        self._score += score_delta

    @staticmethod
    def from_raw_parts(head: Point, tail: List[Point]) -> '_Snake':
        snake = _Snake(head, [])
        snake._tail = tail
        return snake

    def get_state(self) -> SnakeState:
        return SnakeState(
            head = copy(self._head),
            tail = _points_to_directions(self._head, self._tail),
        )

    def move(self, direction: Direction) -> ChangeInFreeCells:
        """Move snake in the specified direction.

        The legality of such a movement is not checked.

        Complexity: O(length). Might be improved in the future if deemed
        reasonable.
        """

        # Moving differs from growing only by not keeping the last segment
        # of the tail.
        change_in_free_cells = self.grow(direction)
        popped_cell = self._tail.pop()
        change_in_free_cells.add_new_free(popped_cell)
        return change_in_free_cells

    def grow(self, direction: Direction) -> ChangeInFreeCells:
        """Grow the snake in the specified direction.

        Whether the snake can actually grow in this direction is not checked.

        Complexity: O(length). Might be improved in the future if deemed
        reasonable.
        """

        old_head = self._head
        self._head = self._head.shift(direction)
        self._tail.insert(0, old_head)
        return ChangeInFreeCells(new_occupied=[self._head], new_free=[])

    def list_occupied_cells(self) -> Generator[Point, None, None]:
        yield self._head
        yield from self._tail

    @property
    def head(self) -> Point:
        return self._head
