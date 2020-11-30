from bot_arena_proto.serialization import (
    DeserializationAdtTagError,
    DeserializationTypeError,
    Primitive,
    PrimitiveSerializable,
    ensure_type,
)

from dataclasses import dataclass
from typing import List, Type, Tuple

from adt import adt, Case

@adt
class Direction:
    Up: Case
    Down: Case
    Left: Case
    Right: Case

    def to_primitive(self) -> Primitive:
        return self.match(
            up = lambda: 'u',
            down = lambda: 'd',
            left = lambda: 'l',
            right = lambda: 'r',
        )

    @classmethod
    def from_primitive(Class: Type['Direction'], p: Primitive) -> 'Direction':
        p = ensure_type(p, str)

        if p == 'u':
            return Class.Up()
        if p == 'd':
            return Class.Down()
        if p == 'l':
            return Class.Left()
        if p == 'r':
            return Class.Right()

        raise DeserializationAdtTagError(Class, p)


@dataclass
class Point:
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
    head: Point
    tail: List[Direction]

    def to_primitive(self) -> Primitive:
        return {'head': self.head.to_primitive(), 'tail': [x.to_primitive() for x in self.tail]}

    @classmethod
    def from_primitive(Class: Type['SnakeState'], p: Primitive) -> 'SnakeState':
        p = ensure_type(p, dict)
        head = Point.from_primitive(p)
        tail = ensure_type(p['tail'], list, 'Snake.tail')
        tail = [Direction.from_primitive(x) for x in tail]
        return Class(head=head, tail=tail)


@dataclass
class FieldState:
    snakes: List[SnakeState]
    objects: List[Tuple[Point, 'Object']]

    def to_primitive(self) -> Primitive:
        return {
            'snakes': [x.to_primitive() for x in self.snakes],
            'objects': [(point.to_primitive(), obj.to_primitive()) for point, obj in self.objects],
        }

    @classmethod
    def from_primitive(Class: Type['FieldState'], p: Primitive) -> 'FieldState':
        p = ensure_type(p, dict)
        snakes = ensure_type(p['snakes'], list)
        objects = ensure_type(p['objects'], list)
        snakes = [SnakeState.from_primitive(x) for x in snakes]
        objects = [(Point.from_primitive(point), Object.from_primitive(obj)) for point, obj in objects]
        return Class(snakes=snakes, objects=objects)

@adt
class Object:
    Food: Case

    def to_primitive(self) -> Primitive:
        return self.match(food = lambda: 'f')

    @classmethod
    def from_primitive(Class: Type['Object'], p: Primitive) -> 'Object':
        p = ensure_type(p, str)
        if p == 'f':
            return Class.Food()
        raise DeserializationAdtTagError(Class, p)


@adt
class Action:
    Move: Case['Direction']

    def to_primitive(self) -> Primitive:
        return self.match(move = lambda direction: ['m', direction.to_primitive()])

    @classmethod
    def from_primitive(Class: Type['Action'], p: Primitive) -> 'Action':
        [tag, *data] = ensure_type(p, list)
        tag = ensure_type(tag, str)
        if tag == 'm':
            return Action.Move(Direction.from_primitive(data[0]))
        raise DeserializationAdtTagError(Class, tag)


