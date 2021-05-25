from bot_arena_proto.serialization import (
    Primitive,
    DeserializationAdtTagError,
    ensure_type,
    wrap_deserialization_errors,
)

from dataclasses import dataclass
from typing import Type, cast


__all__ = ['Event']


@dataclass
class Event:
    """An event that is reported to a client."""

    name: str
    data: Primitive
    must_know: bool

    def to_primitive(self) -> Primitive:
        return {
            'name': self.name,
            'data': self.data,
            'must_know': self.must_know,
        }

    @classmethod
    @wrap_deserialization_errors
    def from_primitive(Class: Type['Event'], p: Primitive) -> 'Event':
        p = ensure_type(p, dict)
        name = ensure_type(p['name'], str)
        data = cast(Primitive, p['data'])
        must_know = ensure_type(p['must_know'], bool)
        return Event(name=name, data=data, must_know=must_know)
