from bot_arena_server.client_name import ClientName
from bot_arena_server.room_mapping import RoomMapping

import copy
import secrets
from dataclasses import dataclass
from typing import Dict, Set, Any

from bot_arena_proto.data import RoomOpenness, FoodRespawnBehavior
from loguru import logger # type: ignore


class PropertyAccessError(Exception):
    pass


class NoSuchProperty(PropertyAccessError):
    def __init__(self, property_name: str) -> None:
        super().__init__(property_name)
        self._property_name = property_name

    def __repr__(self) -> str:
        return f'No such room property: "{self._property_name}"'


class PropertyAccessDenied(PropertyAccessError):
    def __init__(self, property_name: str) -> None:
        super().__init__(property_name)
        self._property_name = property_name

    def __repr__(self) -> str:
        return f'Access denied to property "{self._property_name}"'


class PropertyReadOnly(PropertyAccessError):
    def __init__(self, property_name: str) -> None:
        super().__init__(property_name)
        self._property_name = property_name

    def __repr__(self) -> str:
        return f'Property "{self._property_name}" cannot be written to'


@dataclass
class RoomDetails:
    admins: Set[str]
    name: str
    min_players: int
    max_players: int
    snake_len: int
    field_width: int
    field_height: int
    num_food_items: int
    respawn_food: FoodRespawnBehavior
    open: RoomOpenness
    game_started: bool

    def strip_private_info(self) -> 'RoomDetails':
        result = copy.copy(self)
        result.open = result.open.match(
            open = lambda: RoomOpenness.OPEN(),
            closed = lambda: RoomOpenness.CLOSED(),
            whitelist = lambda whitelist: RoomOpenness.WHITELIST(whitelist),
            password = lambda password: RoomOpenness.PASSWORD(''),
        ) # type: ignore
        return result


def generate_room_id() -> str:
    return secrets.token_hex(8)


class RoomManager:
    def __init__(self) -> None:
        self._mapping = RoomMapping()
        self._alias_map: Dict[str, str] = {}
        self._rooms: Dict[str, RoomDetails] = {}

    def create_room(self, invoking_client: ClientName) -> None:
        room_id = generate_room_id()

        # Precondition: room must not exist (always holds unless there is an unlikely id collision
        # or a bug) and the client must be in the hub.
        # TODO: maybe handle id collisions gracefully.
        self._mapping.check_that_client_is_in_hub(invoking_client)
        self._mapping.check_that_room_does_not_exist(room_id)
        assert room_id not in self._alias_map

        # We have checked all the necessary preconditions and may now proceed.

        logger.info('{} creates a room {!r}', invoking_client, room_id)
        self._mapping.add_room(room_id)
        self._mapping.add_client_to_room(room_id, invoking_client)
        self._alias_map[room_id] = room_id
        self._rooms[room_id] = RoomDetails(
            admins = {str(invoking_client)},    # TODO: maybe change this behavior for viewers
            name = room_id,
            min_players = 2,
            max_players = 2,
            snake_len = 5,
            field_width = 40,
            field_height = 40,
            num_food_items = 3,
            respawn_food = FoodRespawnBehavior.YES(),
            open = RoomOpenness.CLOSED(),
            game_started = False,
        )

    def handle_room_quit(self, invoking_client: ClientName) -> None:
        # Precondition: client is in a room, where a game has not yet started.
        room_id = self._mapping.get_room_with_client(invoking_client)
        room = self._rooms[room_id]
        if room.game_started:
            raise Exception('The game in your room has already started')

        logger.info('{} leaves the room {!r}', invoking_client, room.name)

        # TODO: maybe add a check to ensure that at least one admin
        # is always in the room.
        self._mapping.remove_client_from_room(invoking_client)
        remaining_clients = self._mapping.list_clients_in_a_room(room_id)

        # If nobody is left in the room, it should be deleted.
        if len(list(remaining_clients)) == 0:
            self.remove_room(room_id)
            return

        # If the client was an admin, delete it from this list
        room.admins.discard(str(invoking_client))

    def remove_room(self, room_name: str) -> None:
        # Precondition: room must exist.
        room_id = self.room_name_to_id(room_name)
        self._mapping.check_that_room_exists(room_id)

        logger.info('Removing room {!r}', room_name)
        self._mapping.remove_room(room_id)
        room = self._rooms[room_id]
        self._alias_map.pop(room.name)
        self._alias_map.pop(room_id, None)

    def _rename_room(self, room_name: str, new_name: str) -> None:
        check_that_room_name_is_valid(new_name)
        logger.info('Renaming room {!r} -> {!r}', room_name, new_name)
        room_id = self.room_name_to_id(room_name)

        if room_name != room_id:
            self._alias_map.pop(room_name)

        self._alias_map[new_name] = room_id

    def room_name_to_id(self, room_name: str) -> str:
        return self._alias_map[room_name]

    def handle_room_entry(self, invoking_client: ClientName, room_name: str) -> None:
        # Precondition: room must exist, the client must be able to enter it,
        # the client must be in the hub, and the game must not have started.
        room_id = self.room_name_to_id(room_name)
        self._mapping.check_that_room_exists(room_id)
        self._mapping.check_that_client_is_in_hub(invoking_client)
        room = self._rooms[room_id]
        if room.game_started:
            raise Exception('The game in this room has already started')

        logger.info('{!r} enters toom {!r}', invoking_client, room_name)

    def get_room_properties(self, invoking_client: ClientName) -> Dict[str, Any]:
        # Precondition: client must be in a room and a game must not have started there.
        self._mapping.check_that_client_is_not_in_hub(invoking_client)
        room_id = self._mapping.get_room_with_client(invoking_client)
        room = self._rooms[room_id]
        if room.game_started:
            raise Exception('The game in your room has already started')

        is_admin = invoking_client in room.admins

        if not is_admin:
            room = room.strip_private_info()

        return {
            'name': room.name,
            'players': [
                str(name)
                for name in self._mapping.list_clients_in_a_room(room_id)
                if name.is_player()
            ],
            'min_players': room.min_players,
            'max_players': room.max_players,
            'snake_len': room.snake_len,
            'field_width': room.field_width,
            'field_height': room.field_height,
            'num_food_items': room.num_food_items,
            'respawn_food': room.respawn_food,
            'open': room.open,
        }

    def set_room_properties(self, invoking_client: ClientName, properties: Dict[str, Any]) -> None:
        # Precondition: client must be in a room and a game must not have started there.
        self._mapping.check_that_client_is_not_in_hub(invoking_client)
        room_id = self._mapping.get_room_with_client(invoking_client)
        room = self._rooms[room_id]
        if room.game_started:
            raise Exception('The game in your room has already started')

        is_admin = invoking_client in room.admins
        if not is_admin:
            raise Exception('You must be an admin to change room properties')

        for key, value in properties.items():
            self._set_room_property(room, key, value)

    def _set_room_property(self, room: RoomDetails, key: str, value: Any) -> None:
        if key == 'name':
            self._rename_room(room.name, value)
        elif key == 'players':
            raise Exception('Property "players" is read-only')
        elif key in {
                'min_players',
                'max_players',
                'snake_len',
                'field_width',
                'field_height',
                'num_food_items',
                'respawn_food',
                'open',
        }:
            setattr(room, key, value)
        else:
            raise Exception(f'Invalid room property name: {key!r}')


def check_that_room_name_is_valid(room_name: str) -> None:
    if not is_room_name_valid(room_name):
        raise ValueError(f'Room name is invalid: {room_name!r}')


def is_room_name_valid(room_name: str) -> bool:
    return room_name.isprintable()
