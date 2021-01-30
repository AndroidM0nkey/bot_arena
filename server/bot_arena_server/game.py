from copy import copy
from dataclasses import dataclass
from typing import List, Callable, Tuple, Dict, Set, Generator

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


@dataclass
class ChangeInFreeCells:
    new_free: List[Point]
    new_occupied: List[Point]


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


def _generate_snake(i: int) -> '_Snake':
    # TODO: generate snakes in a more randomized way
    return _Snake(
        head = Point(2 * i, 5),
        tail = [Direction.DOWN(), Direction.DOWN()],
    )


class Game:
    def __init__(self, field_width: int, field_height: int, snake_names: List[str]):
        snakes = {name: _generate_snake(i) for i, name in enumerate(snake_names)}

        # TODO: generate objects

        self._field = Field(
            width = field_width,
            height = field_height,
            snakes = snakes,
            objects = [],
        )

    @property
    def field(self) -> 'Field':
        return self._field

    def take_turn(self, name: str, action: Action) -> MoveResult:
        return action.match(
            move = lambda direction: self.field.move_snake(name, direction),
        )

    def info(self) -> GameInfo:
        return GameInfo(field_width=self._field.width, field_height=self._field.height)


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

    def move_snake(self, name: str, direction: Direction) -> MoveResult:
        if name not in self._snakes:
            raise NoSuchSnakeError(name)

        snake = self._snakes[name]

        destination = snake.head.shift(direction)
        if not self.is_cell_passable(destination):
            return MoveResult.CRASH()

        if destination in self._objects:
            obj = self._objects[destination]
            return obj.match(
                food = lambda: self._consume_food(snake, direction)
            )

        # TODO: pick objects
        change_in_free_cells = snake.move(direction)
        self._update_occupied_cells(change_in_free_cells)

        return MoveResult.OK()

    def _consume_food(self, snake: '_Snake', direction: Direction) -> MoveResult:
        self._update_occupied_cells(snake.grow(direction))
        return MoveResult.OK()

    def _update_occupied_cells(self, change_in_free_cells: ChangeInFreeCells) -> None:
        for cell in change_in_free_cells.new_occupied:
            self._occupied_cells.add(cell)

        for cell in change_in_free_cells.new_free:
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
        change_in_free_cells.new_occupied.append(popped_cell)
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
