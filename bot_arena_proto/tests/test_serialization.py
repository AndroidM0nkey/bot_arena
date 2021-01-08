from bot_arena_proto.serialization import PrimitiveSerializable, Primitive

from dataclasses import dataclass
from typing import Type, List, Dict

@dataclass
class Foo(PrimitiveSerializable):
    data: str

    def to_primitive(self) -> Primitive:
        return self.data

    @classmethod
    def from_primitive(Class: Type['Foo'], p: Primitive) -> 'Foo':
        assert isinstance(p, str)
        return Class(data=p)

@dataclass
class Bar(PrimitiveSerializable):
    a: List[int]
    b: Dict[str, List[bool]]
    c: int

    def to_primitive(self) -> Primitive:
        return {
            'a': self.a,
            'b': self.b,
            'c': self.c,
        }

    @classmethod
    def from_primitive(Class: Type['Bar'], p: Primitive) -> 'Bar':
        assert isinstance(p, dict)
        return Class(a=p['a'], b=p['b'], c=p['c'])


    def __eq__(self, other) -> bool:
        if not isinstance(other, Bar):
            return False
        return self.a == other.a and self.b == other.b and self.c == other.c


def test_foo():
    foo = Foo(data="hi")
    assert foo.to_primitive() == "hi"
    assert Foo.from_primitive("test").data == "test"
    foo_enc = foo.to_bytes()
    foo_dec = Foo.from_bytes(foo_enc)
    assert foo.data == foo_dec.data


def test_bar():
    VALUE_A = [3, 1, 4, 1, 5]
    VALUE_B = {"hi": [False, True, True], "bye": [True]}
    VALUE_C = 1.96
    PRIMITIVE = {"a": VALUE_A, "b": VALUE_B, "c": VALUE_C}

    bar = Bar(a=VALUE_A, b=VALUE_B, c=VALUE_C)
    assert bar.to_primitive() == PRIMITIVE
    assert Bar.from_primitive(PRIMITIVE) == bar
    bar_enc = bar.to_bytes()
    bar_dec = Bar.from_bytes(bar_enc)
    assert bar == bar_dec
