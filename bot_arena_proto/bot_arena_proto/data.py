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


__all__ = [
    'Action',
    'Direction',
    'FieldState',
    'Object',
    'Point',
    'SnakeState',
]


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

    def __hash__(self) -> int:
        a = self.match(
            up = lambda: 0,
            down = lambda: 1,
            left = lambda: 2,
            right = lambda: 3,
        )

        return a ^ 0x7843c6aab56971b4


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

    def shift(self, direction: Direction) -> 'Point':
        dx, dy = direction.match(
            up = lambda: (0, 1),
            down = lambda: (0, -1),
            left = lambda: (-1, 0),
            right = lambda: (1, 0),
        )

        return Point(x = self.x + dx, y = self.y + dy)

    def __hash__(self) -> int:
        return hash((self.x, self.y)) ^ 0xdd77ab420fecfdb9


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


@adt
class FoodRespawnBehavior:
    """Determines how the food is respawned."""
    YES: Case
    NO: Case
    RANDOM: Case[float]

    def to_primitive(self) -> Primitive:
        return self.match(
            yes = lambda: ['yes'],
            no = lambda: ['no'],
            random = lambda p: ['random', p],
        ) # type: ignore

    @classmethod
    def from_primitive(Class: Type['FoodRespawnBehavior'], p: Primitive) -> 'FoodRespawnBehavior':
        [tag, *data] = ensure_type(p, list)
        tag = ensure_type(tag, str)
        if tag == 'yes':
            return FoodRespawnBehavior.YES()
        if tag == 'no':
            return FoodRespawnBehavior.NO()
        if tag == 'random':
            p_value = ensure_type(data[0], float)
            if not 0.0 <= p_value <= 1.0:
                raise ValueError(f'Invalid deserialized p: {p_value}')
            return FoodRespawnBehavior.RANDOM(p_value)
        raise DeserializationAdtTagError(Class, tag)


@adt
class RoomOpenness:
    """Determines who can join a room."""
    OPEN: Case
    CLOSED: Case
    WHITELIST: Case[List[str]]
    PASSWORD: Case[str]

    def to_primitive(self) -> Primitive:
        return self.match(
            open = lambda: ['open'],
            closed = lambda: ['closed'],
            whitelist = lambda whitelist: ['whitelist', whitelist],
            password = lambda password: ['password', password],
        ) # type: ignore

    @classmethod
    def from_primitive(Class: Type['RoomOpenness'], p: Primitive) -> 'RoomOpenness':
        [tag, *data] = ensure_type(p, list)
        tag = ensure_type(tag, str)
        if tag == 'open':
            return RoomOpenness.OPEN()
        if tag == 'close':
            return RoomOpenness.CLOSED()
        if tag == 'whitelist':
            players = ensure_type(data[0], list)
            players_sanitized = [ensure_type(pl, str) for pl in players]
            return RoomOpenness.WHITELIST(players_sanitized)
        if tag == 'password':
            password = ensure_type(data[0], str)
            return RoomOpenness.PASSWORD(password)
        raise DeserializationAdtTagError(Class, tag)


@dataclass(frozen=True)
class RoomInfo:
    id: str
    name: str
    players: List[str]
    min_players: int
    max_players: int
    can_join: str

    def __post_init__(self) -> None:
        can_join_variants = {'yes', 'no', 'whitelist', 'password'}
        if self.can_join not in can_join_variants:
            raise ValueError(f'RoomInfo.can_join must be one of {can_join_variants}')

    def to_primitive(self) -> Primitive:
        return {
            'id': self.id,
            'name': self.name,
            'players': self.players,
            'min_players': self.min_players,
            'max_players': self.max_players,
            'can_join': self.can_join,
        }

    @classmethod
    def from_primitive(Class: Type['RoomInfo'], p: Primitive) -> 'RoomInfo':
        p = ensure_type(p, dict)
        init_kwargs = {
            'id': ensure_type(p['id'], str),
            'name': ensure_type(p['name'], str),
            'min_players': ensure_type(p['min_players'], int),
            'max_players': ensure_type(p['max_players'], int),
            'can_join': ensure_type(p['can_join'], str),
        }

        players = ensure_type(p['players'], list)
        players_sanitized = [ensure_type(pl, str) for pl in players]
        init_kwargs['players'] = players
        return RoomInfo(**init_kwargs)  # type: ignore

