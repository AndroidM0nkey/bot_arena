from bot_arena_proto.data import FieldState, SnakeState, Action, Direction, Point, Object
from bot_arena_proto.event import Event
from bot_arena_proto.message import Message

import copy
import itertools

import pytest


def test_basic_soundness():
    samples = [
        Message.CLIENT_HELLO('Bot 1'), Message.CLIENT_HELLO('Bot 2'),
        Message.SERVER_HELLO(),
        Message.YOUR_TURN(),
        Message.READY(),
        Message.NEW_FIELD_STATE(
            FieldState(
                snakes = [SnakeState(head=Point(4, 5), tail=[Direction.UP()])],
                objects = [],
            )
        ),
        Message.NEW_FIELD_STATE(
            FieldState(
                snakes = [],
                objects = [],
            )
        ),
        Message.ACT(Action.MOVE(Direction.LEFT())), Message.ACT(Action.MOVE(Direction.UP())),
        Message.EVENT_HAPPENED(Event.GAME_FINISHED()), Message.EVENT_HAPPENED(Event.SNAKE_DIED('Bob')),
        Message.OK(),
        Message.ERR('foo'),
        Message.ERR('bar'),
    ]

    n = len(samples)
    for i, j in itertools.product(range(len(samples)), repeat=2):
        a = samples[i]
        b = samples[j]
        if i == j:
            assert a == b
            c = copy.deepcopy(a)
            assert a is not c
            assert a == c
        else:
            assert a != b


class TestBasicSerde:
    @staticmethod
    def test_client_hello():
        assert Message.CLIENT_HELLO('Bob').to_primitive() == ['ClientHello', 'Bob']
        assert Message.from_primitive(['ClientHello', 'Sam']) == Message.CLIENT_HELLO('Sam')

    @staticmethod
    def test_server_hello():
        assert Message.SERVER_HELLO().to_primitive() == ['ServerHello']
        assert Message.from_primitive(['ServerHello']) == Message.SERVER_HELLO()

    @staticmethod
    def test_your_turn():
        assert Message.YOUR_TURN().to_primitive() == ['YourTurn']
        assert Message.from_primitive(['YourTurn']) == Message.YOUR_TURN()

    @staticmethod
    def test_ready():
        assert Message.READY().to_primitive() == ['Ready']
        assert Message.from_primitive(['Ready']) == Message.READY()

    @staticmethod
    def test_new_field_state():
        m1 = Message.NEW_FIELD_STATE(
            FieldState(
                snakes = {
                    'conda': SnakeState(head=Point(1, 4), tail=[Direction.LEFT()]),
                },
                objects = [
                    (Point(3, 1), Object.FOOD()),
                ]
            )
        )
        p1 = [
            'NewFieldState',
            {
                'snakes': {'conda': {'head': [1, 4], 'tail': ['l']}},
                'objects': [[[3, 1], 'f']],
            },
        ]
        m2 = Message.NEW_FIELD_STATE(
            FieldState(
                snakes = {
                    'py': SnakeState(head=Point(4, 3), tail=[Direction.UP()]),
                },
                objects = [
                    (Point(2, 2), Object.FOOD()),
                ]
            )
        )
        p2 = [
            'NewFieldState',
            {
                'snakes': {'py': {'head': [4, 3], 'tail': ['u']}},
                'objects': [[[2, 2], 'f']],
            },
        ]

        assert m1.to_primitive() == p1
        assert Message.from_primitive(p1) == m1
        assert m2.to_primitive() == p2
        assert Message.from_primitive(p2) == m2

    @staticmethod
    def test_act():
        assert Message.ACT(Action.MOVE(Direction.DOWN())).to_primitive() == ['Act', ['m', 'd']]
        assert Message.from_primitive(['Act', ['m', 'u']]) == Message.ACT(Action.MOVE(Direction.UP()))

    @staticmethod
    def test_event_happened():
        m1 = Message.EVENT_HAPPENED(Event.GAME_FINISHED())
        p1 = ['EventHappened', ['GameFinished']]
        m2 = Message.EVENT_HAPPENED(Event.SNAKE_DIED('Abc'))
        p2 = ['EventHappened', ['SnakeDied', {'name': 'Abc'}]]

        assert m1.to_primitive() == p1
        assert Message.from_primitive(p1) == m1
        assert m2.to_primitive() == p2
        assert Message.from_primitive(p2) == m2

    @staticmethod
    def test_ok():
        assert Message.OK().to_primitive() == ['Ok']
        assert Message.from_primitive(['Ok']) == Message.OK()

    @staticmethod
    def test_err():
        assert Message.ERR('2 + 2 != 4').to_primitive() == ['Err', '2 + 2 != 4']
        assert Message.from_primitive(['Err', 'Server caught fire']) == Message.ERR('Server caught fire')
