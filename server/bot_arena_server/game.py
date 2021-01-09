from copy import copy
from typing import List

from bot_arena_proto.data import SnakeState, Direction, Point


__all__ = [
    #'Game',
    #'Field',
]


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
