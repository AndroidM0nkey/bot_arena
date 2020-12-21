from bot_arena_proto.serialization import (
    DeserializationAdtTagError,
    DeserializationTypeError,
    Primitive,
    PrimitiveSerializable,
    ensure_type,
)

from dataclasses import dataclass
from typing import List, Type, Tuple, Dict

from adt import adt, Case


@adt
class Direction:
    """A direction in which a snake can move each turn."""

    UP: Case
    DOWN: Case
    LEFT: Case
    RIGHT: Case

    def to_primitive(self) -> Primitive:
        return self.match(
            up = lambda: 'u',
            down = lambda: 'd',
            left = lambda: 'l',
            right = lambda: 'r',
        )  # type: ignore
        # mypy complains unreasonably here

    @classmethod
    def from_primitive(Class: Type['Direction'], p: Primitive) -> 'Direction':
        p = ensure_type(p, str)

        if p == 'u':
            return Class.UP()
        if p == 'd':
            return Class.DOWN()
        if p == 'l':
            return Class.LEFT()
        if p == 'r':
            return Class.RIGHT()

        raise DeserializationAdtTagError(Class, p)


@dataclass
class Point:
    """A 2D point with integer coords representing a cell of the game field."""

    x: int
    y: int

    def to_primitive(self) -> Primitive:
        return [self.x, self.y]

    @classmethod
    def from_primitive(Class: Type['Point'], p: Primitive) -> 'Point':
        p = ensure_type(p, list)
        [x, y] = p
        x = ensure_type(x, int)
        y = ensure_type(y, int)
        return Class(x=x, y=y)


@dataclass
class SnakeState:
    """An object fully describing the precise position of a snake."""

    head: Point
    tail: List[Direction]

    def to_primitive(self) -> Primitive:
        return {'head': self.head.to_primitive(), 'tail': [x.to_primitive() for x in self.tail]}

    @classmethod
    def from_primitive(Class: Type['SnakeState'], p: Primitive) -> 'SnakeState':
        p = ensure_type(p, dict)
        head = Point.from_primitive(p['head'])
        tail = ensure_type(p['tail'], list, 'Snake.tail')
        tail = [Direction.from_primitive(x) for x in tail]
        return Class(head=head, tail=tail)


@dataclass
class FieldState:
    """An object fully describing the current state of the game field (except its size).

    `snakes` stores the information about snakes. It is a dictionary where keys are snake names,
    and values are the corresponding SnakeState objects.

    `objects` stores the information about in-game objects. Each entry of the list is
    a tuple which contains (1) the position of an object in the field and (2)
    the object itself.
    """

    snakes: Dict[str, SnakeState]
    objects: List[Tuple[Point, 'Object']]

    def to_primitive(self) -> Primitive:
        return {
            'snakes': {name: snake.to_primitive() for name, snake in self.snakes.items()},
            'objects': [[point.to_primitive(), obj.to_primitive()] for point, obj in self.objects],
        }

    @classmethod
    def from_primitive(Class: Type['FieldState'], p: Primitive) -> 'FieldState':
        p = ensure_type(p, dict)
        snakes = ensure_type(p['snakes'], dict)
        objects = ensure_type(p['objects'], list)
        snakes = {ensure_type(key, str): SnakeState.from_primitive(value) for key, value in snakes.items()}
        objects = [(Point.from_primitive(point), Object.from_primitive(obj)) for point, obj in objects]
        return Class(snakes=snakes, objects=objects)

@adt
class Object:
    """An in-game object.

    Currently, the only type of such an object is food, which increases the length of a snake."""

    FOOD: Case

    def to_primitive(self) -> Primitive:
        return self.match(food = lambda: 'f')  # type: ignore
        # mypy complains unreasonably here

    @classmethod
    def from_primitive(Class: Type['Object'], p: Primitive) -> 'Object':
        p = ensure_type(p, str)
        if p == 'f':
            return Class.FOOD()
        raise DeserializationAdtTagError(Class, p)


@adt
class Action:
    """An action a player controlling a snake may perform.

    Currently, the only such action is to instruct a snake move in a certain direction."""

    MOVE: Case['Direction']

    def to_primitive(self) -> Primitive:
        return self.match(move = lambda direction: ['m', direction.to_primitive()])  # type: ignore
        # mypy complains unreasonably here

    @classmethod
    def from_primitive(Class: Type['Action'], p: Primitive) -> 'Action':
        [tag, *data] = ensure_type(p, list)
        tag = ensure_type(tag, str)
        if tag == 'm':
            return Action.MOVE(Direction.from_primitive(data[0]))
        raise DeserializationAdtTagError(Class, tag)
