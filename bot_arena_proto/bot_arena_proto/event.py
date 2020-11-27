from bot_arena_proto.serialization import PrimitiveSerializable, Primitive, SerializableSelfType

from abc import abstractmethod
from dataclasses import dataclass
from typing import Type, TypeVar, Callable, Tuple, Any

_T = TypeVar('_T')


class Event(PrimitiveSerializable):
    # Just some ugly emulation of algebraic data type
    def match(
        self, *,
        snake_died: Callable[['SnakeDied'], _T],
        game_finished: Callable[['GameFinished'], _T],
        game_started: Callable[['GameStarted'], _T],
    ) -> _T:
        func: Any

        if isinstance(self, SnakeDied):
            func = snake_died
        elif isinstance(self, GameFinished):
            func = game_finished
        elif isinstance(self, GameStarted):
            func = game_started
        else:
            raise TypeError(f'Unknown event type: {type(self)}')

        return func(self)

    def to_primitive(self) -> Primitive:
        return [self.type_string(), self.to_primitive_impl()]

    def type_string(self) -> str:
        return self.match(
            snake_died = lambda _: 'SnakeDied',
            game_started = lambda _: 'GameStarted',
            game_finished = lambda _: 'GameFinished',
        )

    @staticmethod
    def type_string_to_subclass(type_string: str) -> Type['Event']:
        if type_string == 'SnakeDied':
            return SnakeDied
        if type_string == 'GameStarted':
            return GameStarted
        if type_string == 'GameFinished':
            return GameFinished
        raise ValueError(f'Unknown event type string: {repr(type_string)}')

    @classmethod
    def from_primitive(Class: Type['Event'], p: Primitive) -> 'Event':
        if not isinstance(p, list):
            raise TypeError(f'Bad deserialized type: expected list, got {type(p)}')

        [type_string, inner_primitive] = p
        if not isinstance(type_string, str):
            raise TypeError(f'Bad deserialized type: expected str, got {type(type_string)}')

        Subclass = Class.type_string_to_subclass(type_string)
        return Subclass.from_primitive_impl(inner_primitive)

    @abstractmethod
    def to_primitive_impl(self) -> Primitive:
        ...

    @classmethod
    @abstractmethod
    def from_primitive_impl(Class: Type[SerializableSelfType], p: Primitive) -> SerializableSelfType:
        ...


@dataclass
class SnakeDied(Event):
    snake_name: str

    def to_primitive_impl(self) -> Primitive:
        return self.snake_name

    @classmethod
    def from_primitive_impl(Class: Type['SnakeDied'], p: Primitive) -> 'SnakeDied':
        if not isinstance(p, str):
            raise TypeError(f'Bad deserialized type: expected str, got {type(p)}')
        return SnakeDied(snake_name=p)


class GameFinished(Event):
    def to_primitive_impl(self) -> Primitive:
        return None

    @classmethod
    def from_primitive_impl(Class: Type['GameFinished'], p: Primitive) -> 'GameFinished':
        if p is not None:
            raise TypeError(f'Bad deserialized type: expected NoneType, got {type(p)}')
        return GameFinished()


@dataclass
class GameStarted(Event):
    field_size: Tuple[int, int]

    def to_primitive_impl(self) -> Primitive:
        return list(self.field_size)

    @classmethod
    def from_primitive_impl(Class: Type['GameStarted'], p: Primitive) -> 'GameStarted':
        if not isinstance(p, list):
            raise TypeError(f'Bad deserialized type: expected list, got {type(p)}')
        [width, height] = p
        if not isinstance(width, int):
            raise TypeError(f'Bad deserialized type of `width`: expected int, got {type(width)}')
        if not isinstance(height, int):
            raise TypeError(f'Bad deserialized type of `height`: expected int, got {type(height)}')
        return GameStarted(field_size=(width, height))
