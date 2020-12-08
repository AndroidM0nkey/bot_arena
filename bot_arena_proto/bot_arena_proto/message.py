from bot_arena_proto.data import Action, FieldState
from bot_arena_proto.event import Event
from bot_arena_proto.serialization import (
    DeserializationAdtTagError,
    DeserializationLogicError,
    Primitive,
    PrimitiveSerializable,
    ensure_type,
)

from adt import adt, Case
from dataclasses import dataclass
from typing import Type, cast


@adt
class Message(PrimitiveSerializable):
    CLIENT_HELLO: Case[str]
    SERVER_HELLO: Case
    YOUR_TURN: Case
    READY: Case
    NEW_FIELD_STATE: Case['FieldState']
    ACT: Case['Action']
    EVENT_HAPPENED: Case['Event']
    OK: Case
    ERR: Case[str]

    def to_primitive(self) -> Primitive:
        return cast(
            Primitive,
            self.match(
                client_hello = lambda name: ['ClientHello', name],
                server_hello = lambda: ['ServerHello'],
                your_turn = lambda: ['YourTurn'],
                ready = lambda: ['Ready'],
                new_field_state = lambda state: ['NewFieldState', state.to_primitive()],
                act = lambda action: ['Act', action.to_primitive()],
                event_happened = lambda event: ['EventHappened', event.to_primitive()],
                ok = lambda: ['Ok'],
                err = lambda message: ['Err', message],
            ),
        )

    @classmethod
    def from_primitive(Class: Type['Message'], p: Primitive) -> 'Message':
        p = ensure_type(p, list)
        [tag, *data] = p
        if len(data) > 1:
            raise DeserializationLogicError(
                f'`data` array is supposed to contain no more than 1 element, but its length is {len(data)}'
            )

        if tag == 'ClientHello':
            name = ensure_type(data[0], str)
            return Message.CLIENT_HELLO(name)
        if tag == 'ServerHello':
            return Message.SERVER_HELLO()
        if tag == 'YourTurn':
            return Message.YOUR_TURN()
        if tag == 'Ready':
            return Message.READY()
        if tag == 'NewFieldState':
            state = FieldState.from_primitive(data[0])
            return Message.NEW_FIELD_STATE(state)
        if tag == 'Act':
            action = Action.from_primitive(data[0])
            return Message.ACT(action)
        if tag == 'EventHappened':
            event = Event.from_primitive(data[0])
            return Message.EVENT_HAPPENED(event)
        if tag == 'Ok':
            return Message.OK()
        if tag == 'Err':
            error_message = ensure_type(data[0], str)
            return Message.ERR(error_message)
        raise DeserializationAdtTagError(Message, tag)

