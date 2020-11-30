from bot_arena_proto.data import Action, FieldState
from bot_arena_proto.event import Event
from bot_arena_proto.serialization import (
    DeserializationAdtTagError,
    DeserializationLogicError,
    Primitive,
    ensure_type,
)

from adt import adt, Case
from dataclasses import dataclass
from typing import Type, cast


@adt
class Message:
    ClientHello: Case[str]
    ServerHello: Case
    YourTurn: Case
    Ready: Case
    NewFieldState: Case['FieldState']
    Act: Case['Action']
    EventHappened: Case['Event']
    Ok: Case
    Err: Case[str]

    def to_primitive(self) -> Primitive:
        return cast(
            Primitive,
            self.match(
                clienthello = lambda name: ['ClientHello', name],
                serverhello = lambda: ['ServerHello'],
                yourturn = lambda: ['YourTurn'],
                ready = lambda: ['Ready'],
                newfieldstate = lambda state: ['NewFieldState', state.to_primitive()],
                act = lambda action: ['Act', action.to_primitive()],
                eventhappened = lambda event: ['EventHappened', event.to_primitive()],
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
            return Message.ClientHello(name)
        if tag == 'ServerHello':
            return Message.ServerHello()
        if tag == 'YourTurn':
            return Message.YourTurn()
        if tag == 'Ready':
            return Message.Ready()
        if tag == 'NewFieldState':
            state = FieldState.from_primitive(data[0])
            return Message.NewFieldState(state)
        if tag == 'Act':
            action = Action.from_primitive(data[0])
            return Message.Act(action)
        if tag == 'EventHappened':
            event = Event.from_primitive(data[0])
            return Message.EventHappened(event)
        if tag == 'Ok':
            return Message.Ok()
        if tag == 'Err':
            error_message = ensure_type(data[0], str)
            return Message.Err(error_message)
        raise DeserializationAdtTagError(Message, tag)

