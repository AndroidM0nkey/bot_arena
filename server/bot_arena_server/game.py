import random
from copy import copy
from dataclasses import dataclass
from typing import List, Callable, Tuple, Dict, Set, Generator, Optional, Iterable

from adt import adt, Case
from bot_arena_proto.data import SnakeState, Direction, Point, Object, FieldState, Action
from bot_arena_proto.session import GameInfo


__all__ = [
    'Game',
    'Field',
    'IllegalAction',
    'InvalidMoveError',
    'NoSuchSnakeError',
    'MoveResult',
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
    def __init__(self, field_width: int, field_height: int, snake_names: List[str]):
        self._field = Field(
            width = field_width,
            height = field_height,
            snakes = {},
            objects = [],
        )

        for name in snake_names:
            # TODO: make the length configurable
            snake = _generate_snake(self._field, 5)
            self._field.add_snake(name, snake)

        # TODO: make the number of objects configurable
        for i in range(5):
            self._field.place_object_randomly(Object.FOOD())

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

    def is_finish_condition_satisfied(self) -> bool:
        # TODO: make the finish condition configurable.
        return self.field.count_alive_players() <= 1


class Field:
    def __init__(
        self,
        width: int,
        height: int,
        snakes: Dict[str, '_Snake'],
        objects: List[Tuple[Point, Object]],
    ) -> None:
        self._width = width
        self._height = height
        self._snakes = snakes
        self._objects: Dict[Point, Object] = dict(objects)
        self._occupied_cells: Set[Point] = set()
        for snake in snakes.values():
            self._occupied_cells.update(snake.list_occupied_cells())

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

    def move_snake(self, name: str, direction: Direction) -> MoveResult:
        if name not in self._snakes:
            raise NoSuchSnakeError(name)

        snake = self._snakes[name]

        destination = snake.head.shift(direction)
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

        # TODO: pick objects
        change_in_free_cells = snake.move(direction)
        self._update_occupied_cells(change_in_free_cells)

        return MoveResult.OK()

    def _consume_food(self, snake: '_Snake', direction: Direction) -> MoveResult:
        self._update_occupied_cells(snake.grow(direction))
        self._objects.pop(snake.head)
        return MoveResult.OK()

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
        return self._width

    @property
    def height(self) -> int:
        return self._height

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

    def is_cell_completely_free(self, cell: Point) -> bool:
        return (cell in self) and (cell not in self._occupied_cells) and (cell not in self._objects)

    def _place_object_at(self, obj: Object, point: Point) -> None:
        self._objects[point] = obj

    def add_snake(self, snake_name: str, snake: '_Snake') -> None:
        if snake_name in self._snakes:
            raise KeyError(f'Snake `{snake_name}` is already present on the game field')
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
    def __init__(self, head: Point, tail: List[Direction]):
        self._head = head
        self._tail = _directions_to_points(head, tail)

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
