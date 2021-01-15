from copy import copy
from typing import List, Callable, Tuple, Dict

from adt import adt, Case
from bot_arena_proto.data import SnakeState, Direction, Point, Object, FieldState, Action


__all__ = [
    'Game',
    'Field',
    'IllegalAction',
    'InvalidMoveError',
    'NoSuchSnakeError',
    'MoveResult',
]


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
    def field(self) -> Field:
        return self._field

    def take_turn(self, name: str, action: Action):
        action.match(
            move = lambda direction: self.field.move_snake(name, direction),
        )


class Field:
    def __init__(
        self,
        width: int,
        height: int,
        snakes: Dict[str, '_Snake'],
        objects: List[Tuple[Point, Object]],
    ):
        self._width = width
        self._height = height
        self._snakes = snakes
        self._objects = objects

    def move_snake(self, name: str, direction: Direction) -> MoveResult:
        if name not in self._snakes:
            raise NoSuchSnakeError(name)

        snake = self._snakes[name]

        # TODO: detect collisions
        # TODO: pick objects
        snake.move(direction)
        return MoveResult.OK()

    def get_state(self) -> FieldState:
        return FieldState(snakes=copy(self._snakes), objects=copy(self._objects))


class _Snake:
    def __init__(self, head: Point, tail: List[Direction]):
        self._head = head
        self._tail = tail

    def get_state(self) -> SnakeState:
        # Shallow copying is done because both `self._head` and `self._tail`
        # may change in the runtime, which is absolutely unacceptable for
        # a `SnakeState` object, which is by design a record of static data.
        # Copying prevents this kind of issue, for the price of some small
        # performance (several milliseconds at most for very long snakes;
        # much less for typical, shorter snakes) and memory (several
        # kilobytes, probably?) overhead.
        return SnakeState(head=copy(self._head), tail=copy(self._tail))

    def move(self, direction: Direction):
        """Move snake in the specified direction.

        The legality of such a movement is not checked.

        Complexity: O(length). Might be improved in the future if deemed
        reasonable.
        """

        # Moving differs from growing only by not keeping the last segment
        # of the tail.
        self.grow(direction)
        self._tail.pop()

    def grow(self, direction: Direction):
        """Grow the snake in the specified direction.

        Whether the snake can actually grow in this direction is not checked.

        Complexity: O(length). Might be improved in the future if deemed
        reasonable.
        """

        delta_x, delta_y = direction.match(
            up = lambda: (0, 1),
            down = lambda: (0, -1),
            left = lambda: (-1, 0),
            right = lambda: (1, 0),
        )

        self._head.x += delta_x
        self._head.y += delta_y

        self._tail.insert(0, reverse(direction))


def reverse(direction: Direction) -> Direction:
    return direction.match(
        up = lambda: Direction.DOWN(),
        down = lambda: Direction.UP(),
        left = lambda: Direction.RIGHT(),
        right = lambda: Direction.LEFT(),
    )
