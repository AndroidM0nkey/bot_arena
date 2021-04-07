from bot_arena_proto.data import Action, FieldState, FoodRespawnBehavior, RoomOpenness, RoomInfo
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
from typing import List, Dict, Any, Type, cast


__all__ = ['Message']



def prop_to_primitive(name: str, value: Any) -> Primitive:
    if name == 'players':
        value = ensure_type(value, list)
        value = [ensure_type(s, str) for s in value]
        return value

    if name in {
        'min_players',
        'max_players',
        'snake_len',
        'field_width',
        'field_height',
        'num_food_items',
    }:
        return ensure_type(value, int)

    if name in {'respawn_food', 'open'}:
        return value.to_primitive()

    # fallback
    return value


def prop_from_primitive(name: str, p: Primitive) -> Any:
    if name == 'players':
        p = ensure_type(p, list)
        p = [ensure_type(s, str) for s in p]
        return p

    if name in {
        'min_players',
        'max_players',
        'snake_len',
        'field_width',
        'field_height',
        'num_food_items',
    }:
        return ensure_type(p, int)

    if name == 'respawn_food':
        return FoodRespawnBehavior.from_primitive(p)

    if name == 'open':
        return RoomOpenness.from_primitive(p)

    # fallback
    return p


@adt
class Message(PrimitiveSerializable):
    """A message, a low-level unit of information that is exchanged
    between a client and a server.

    Currently, the following types of messages exist:

    - CLIENT_HELLO:     The message sent by a client when it connects
                        to the server. The name of the player is the
                        only parameter.

    - SERVER_HELLO:     Successful server's response to a CLIENT_HELLO.

    - YOUR_TURN:        A notification sent to a client that their turn
                        has come and they can perform an action (see
                        bot_arena_proto.data.Action and Message.ACT
                        for details).

    - READY:            A notification sent by a client to the server
                        that the client is ready to begin the game.

    - NEW_FIELD_STATE:  A notification from a server to a client that
                        the field state has changed. The new field state
                        is attached as a parameter.

    - ACT:              An instruction sent by a client to the server
                        that this client wants to perform a certain
                        action (see bot_arena_proto.data.Action) with
                        their snake. Only meaningful if it is this
                        client's turn now.

    - OK:               A generic server's response to some client's
                        messages indicating that they were handled
                        without an error. Clients can safely ignore this
                        type of messages.

    - ERR:              A generic server's response to some client's
                        messages indicating that these messages were not
                        handled properly due to an error. A description
                        of the error is attached as a parameter.

    - LIST_ROOMS        A client's request to get the list of all rooms.

    - ENTER_ROOM:       A client's request to enter a specific room.

    - ENTER_ANY_ROOM:   A client's request to enter any room, at the server's
                        discretion.

    - NEW_ROOM:         A client's request to create their own room.

    - LEAVE_ROOM:       A client's request to leave the current room.

    - GET_ROOM_PROPERTIES:
                        A client's request to get all the properties (with values)
                        of the room they are currently in.

    - SET_ROOM_PROPERTIES:
                        A client's request to set properties of the room they are
                        currently in and they are currently an admin of.

    - ROOM_LIST_AVAILABLE:
                        A server's response to the client's LIST_ROOMS with the list
                        of all the rooms and information about them.

    - ROOM_PROPERTIES_AVAILABLE:
                        A server's response to the client's GET_ROOM_PROPERTIES with
                        the dictionary mapping the property names to their values.
    """
    CLIENT_HELLO: Case[str]
    SERVER_HELLO: Case
    YOUR_TURN: Case
    READY: Case
    NEW_FIELD_STATE: Case['FieldState']
    ACT: Case['Action']
    EVENT_HAPPENED: Case['Event']
    OK: Case
    ERR: Case[str]
    LIST_ROOMS: Case
    ENTER_ROOM: Case[str]
    ENTER_ANY_ROOM: Case
    NEW_ROOM: Case
    LEAVE_ROOM: Case
    GET_ROOM_PROPERTIES: Case
    SET_ROOM_PROPERTIES: Case[Dict[str, Any]]
    ROOM_LIST_AVAILABLE: Case[List[RoomInfo]]
    ROOM_PROPERTIES_AVAILABLE: Case[Dict[str, Any]]

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
                list_rooms = lambda: ['ListRooms'],
                enter_room = lambda name: ['EnterRoom', name],
                enter_any_room = lambda: ['EnterAnyRoom'],
                new_room = lambda: ['NewRoom'],
                leave_room = lambda: ['LeaveRoom'],
                get_room_properties = lambda: ['GetRoomProperties'],
                set_room_properties = lambda props: [
                    'SetRoomProperties',
                    {k: prop_to_primitive(k, v) for k, v in props.items()},
                ],
                room_list_available = lambda rooms: [
                    'RoomListAvailable',
                    [r.to_primitive() for r in rooms],
                ],
                room_properties_available = lambda props: [
                    'RoomPropertiesAvailable',
                    {k: prop_to_primitive(k, v) for k, v in props.items()},
                ]
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
        if tag == 'ListRooms':
            return Message.LIST_ROOMS()
        if tag == 'EnterRoom':
            return Message.ENTER_ROOM(ensure_type(data[0], str))
        if tag == 'EnterAnyRoom':
            return Message.ENTER_ANY_ROOM()
        if tag == 'NewRoom':
            return Message.NEW_ROOM()
        if tag == 'LeaveRoom':
            return Message.LEAVE_ROOM()
        if tag == 'GetRoomProperties':
            return Message.GET_ROOM_PROPERTIES()
        if tag == 'SetRoomProperties':
            props = ensure_type(data[0], dict)
            props_sanitized = {
                ensure_type(k, str): prop_from_primitive(k, v)
                for k, v in props.items()
            }
            return Message.SET_ROOM_PROPERTIES(props_sanitized)
        if tag == 'RoomListAvailable':
            rooms = ensure_type(data[0], list)
            rooms_sanitized = [RoomInfo.from_primitive(r) for r in rooms]
            return Message.ROOM_LIST_AVAILABLE(rooms_sanitized)
        if tag == 'RoomPropertiesAvailable':
            props = ensure_type(data[0], dict)
            props_sanitized = {
                ensure_type(k, str): prop_from_primitive(k, v)
                for k, v in props.items()
            }
            return Message.ROOM_PROPERTIES_AVAILABLE(props_sanitized)

        raise DeserializationAdtTagError(Message, tag)

