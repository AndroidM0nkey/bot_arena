from bot_arena_server import password_utils
from bot_arena_server.client_name import ClientName
from bot_arena_server.game import Game
from bot_arena_server.game_config import GameConfig
from bot_arena_server.game_room import GameRoom
from bot_arena_server.pubsub import PublishSubscribeService
from bot_arena_server.room_mapping import RoomMapping

import copy
import math
import secrets
from dataclasses import dataclass
from typing import Dict, Set, Any, Tuple, List, Callable, Coroutine, Iterable, cast, Optional

import curio # type: ignore
from bot_arena_proto.data import RoomOpenness, FoodRespawnBehavior, RoomInfo
from loguru import logger # type: ignore


class ProhibitedAction(Exception):
    pass


class CannotEnterRoom(ProhibitedAction):
    pass


class GameAlreadyStarted(CannotEnterRoom):
    def __init__(self, room_name: str) -> None:
        super().__init__()
        self.room_name = room_name

    def __str__(self) -> str:
        return f'Game in the room {self.room_name!r} has already started'


class RoomIsFull(CannotEnterRoom):
    def __init__(self, room_name: str) -> None:
        super().__init__()
        self.room_name = room_name

    def __str__(self) -> str:
        return f'Room {self.room_name!r} is full'


class RoomIsClosed(CannotEnterRoom):
    def __init__(self, room_name: str) -> None:
        super().__init__()
        self.room_name = room_name

    def __str__(self) -> str:
        return f'Room {self.room_name!r} is closed'


class RoomPasswordIsInvalid(CannotEnterRoom):
    def __init__(self, room_name: str) -> None:
        super().__init__()
        self.room_name = room_name

    def __str__(self) -> str:
        return f'Your password to access the room {self.room_name!r} is not correct'


class NotWhitelisted(CannotEnterRoom):
    def __init__(self, room_name: str) -> None:
        super().__init__()
        self.room_name = room_name

    def __str__(self) -> str:
        return f'You are not in the whitelist for the room {self.room_name!r}'


class PropertyAccessError(Exception):
    pass


class NoSuchProperty(PropertyAccessError):
    def __init__(self, property_name: str) -> None:
        super().__init__(property_name)
        self.property_name = property_name

    def __str__(self) -> str:
        return f'No such room property: {self.property_name!r}'


class PropertyAccessDenied(PropertyAccessError):
    def __init__(self, property_name: str) -> None:
        super().__init__(property_name)
        self.property_name = property_name

    def __str__(self) -> str:
        return f'Access denied to property {self.property_name!r}'


class PropertyReadOnly(PropertyAccessError):
    def __init__(self, property_name: str) -> None:
        super().__init__(property_name)
        self.property_name = property_name

    def __str__(self) -> str:
        return f'Property {self.property_name!r} cannot be written to'


class PropertyValueIsInvalid(PropertyAccessError):
    def __init__(self, property_name: str, explanation: str) -> None:
        super().__init__(property_name)
        self.property_name = property_name
        self.explanation = explanation

    def __str__(self) -> str:
        return f'Invalid value specified for {self.property_name!r}: {self.explanation}'


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
    max_turns: Optional[int]
    turn_timeout_seconds: Optional[float]
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

    def as_game_config(self) -> GameConfig:
        return GameConfig(
            snake_len = self.snake_len,
            field_width = self.field_width,
            field_height = self.field_height,
            num_food_items = self.num_food_items,
            respawn_food = self.respawn_food,
            max_turns = self.max_turns,
        )


def generate_room_id() -> str:
    return secrets.token_hex(8)


class RoomSyncObject:
    def __init__(self):
        self.readiness_set: Set[ClientName] = set()
        self.pubsub: PublishSubscribeService[Tuple[Game, GameRoom]] = PublishSubscribeService()


class RoomManager:
    def __init__(self) -> None:
        self._mapping = RoomMapping()
        self._alias_map: Dict[str, str] = {}
        self._rooms: Dict[str, RoomDetails] = {}
        self._room_sync: Dict[str, RoomSyncObject] = {}

    def create_room(self, invoking_client: ClientName) -> None:
        room_id = generate_room_id()

        # Precondition: room must not exist (always holds unless there is an unlikely id collision
        # or a bug) and the client must be in the hub.
        # TODO: maybe handle id collisions gracefully.
        self._mapping.check_that_client_is_in_hub(invoking_client)
        self._mapping.check_that_room_does_not_exist(room_id)
        assert room_id not in self._alias_map

        # We have checked all the necessary preconditions and may now proceed.

        logger.info('{!r} creates a room {!r}', invoking_client, room_id)
        self._mapping.add_room(room_id)
        self._mapping.add_client_to_room(room_id, invoking_client)
        self._alias_map[room_id] = room_id
        self._rooms[room_id] = RoomDetails(
            admins = {str(invoking_client)},    # TODO: maybe change this behavior for viewers
            name = room_id,
            min_players = 2,
            max_players = 3,
            snake_len = 5,
            field_width = 40,
            field_height = 40,
            num_food_items = 3,
            respawn_food = FoodRespawnBehavior.YES(),
            open = RoomOpenness.CLOSED(),
            max_turns = 1000,
            game_started = False,
            turn_timeout_seconds = None,
        )
        self._room_sync[room_id] = RoomSyncObject()

    def handle_room_quit(self, invoking_client: ClientName) -> None:
        # Precondition: client is in a room, where a game has not yet started.
        room_id = self._mapping.get_room_with_client(invoking_client)
        room = self._rooms[room_id]
        if room.game_started:
            raise GameAlreadyStarted(room.name)

        logger.info('{} leaves the room {!r}', invoking_client, room.name)

        # TODO: maybe add a check to ensure that at least one admin
        # is always in the room.
        self._mapping.remove_client_from_room(invoking_client)
        self._room_sync[room_id].readiness_set.discard(invoking_client)
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
        self._room_sync.pop(room_id)
        self._rooms.pop(room_id)

    def _rename_room(self, room_name: str, new_name: str) -> None:
        check_that_room_name_is_valid(new_name)
        logger.info('Renaming room {!r} -> {!r}', room_name, new_name)
        room_id = self.room_name_to_id(room_name)

        if room_name != room_id:
            self._alias_map.pop(room_name)

        self._alias_map[new_name] = room_id
        self._rooms[room_id].name = new_name

    def room_name_to_id(self, room_name: str) -> str:
        return self._alias_map[room_name]

    def handle_room_entry(self, invoking_client: ClientName, room_name: str, password: Optional[str]) -> None:
        # Precondition: room must exist, the client must be able to enter it,
        # the client must be in the hub, and the game must not have started.
        room_id = self.room_name_to_id(room_name)
        self._mapping.check_that_room_exists(room_id)
        self._mapping.check_that_client_is_in_hub(invoking_client)
        room = self._rooms[room_id]
        if room.game_started:
            raise GameAlreadyStarted(room_name)

        # The resulting number of players must be less than the upper limit on it.
        # Not meeting the lower limit is ok here.
        current_num_players = self._mapping.count_players_in_a_room(room_id)
        resulting_num_players = current_num_players + (1 if invoking_client.is_player() else 0)
        if resulting_num_players > room.max_players:
            raise RoomIsFull(room_name)

        # The room must not be closed.
        def handle_closed_room() -> None:
            raise RoomIsClosed(room_name)

        # And, if it is password-protected, the password must be correct.
        def handle_password_protected_room(correct_password: str) -> None:
            if password is None or (not password_utils.are_passwords_equal(password, correct_password)):
                raise RoomPasswordIsInvalid(room_name)

        def handle_whitelist_protected_room(whitelist: List[str]) -> None:
            # Inefficient, but probably not of a great concern.
            # TODO: put limits on the whitelist size.
            if invoking_client.is_player():
                if str(invoking_client) not in whitelist:
                    raise NotWhitelisted(room_name)
            else:
                if '@viewers' not in whitelist:
                    raise NotWhitelisted(room_name)

        room.open.match(
            open = lambda: None,
            closed = handle_closed_room,
            password = handle_password_protected_room,
            whitelist = handle_whitelist_protected_room,
        ) # type: ignore

        logger.info('{!r} enters room {!r}', invoking_client, room_name)
        self._mapping.add_client_to_room(room_id, invoking_client)

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
            'admins': list(room.admins),
            'min_players': room.min_players,
            'max_players': room.max_players,
            'snake_len': room.snake_len,
            'field_width': room.field_width,
            'field_height': room.field_height,
            'num_food_items': room.num_food_items,
            'respawn_food': room.respawn_food,
            'open': room.open,
            'max_turns': room.max_turns,
            'turn_timeout_seconds': room.turn_timeout_seconds,
        }

    def set_room_properties(self, invoking_client: ClientName, properties: Dict[str, Any]) -> None:
        # Precondition: client must be in a room and a game must not have started there.
        self._mapping.check_that_client_is_not_in_hub(invoking_client)
        room_id = self._mapping.get_room_with_client(invoking_client)
        room = self._rooms[room_id]
        if room.game_started:
            raise Exception('The game in your room has already started')

        is_admin = invoking_client.is_player() and str(invoking_client) in room.admins
        if not is_admin:
            raise Exception('You must be an admin to change room properties')

        # TODO: maybe introduce an all-or-nothing scheme?
        for key, value in properties.items():
            self._set_room_property(room_id, room, key, value)

    def _set_room_property(self, room_id: str, room: RoomDetails, key: str, value: Any) -> None:
        if key == 'name':
            self._rename_room(room.name, value)

        elif key == 'players':
            raise Exception('Property "players" is read-only')

        elif key == 'admins':
            players = set(self.list_players_in_a_room(room.name))
            admins = value
            for player_name in admins:
                if player_name not in players:
                    raise PropertyValueIsInvalid(key, f'{player_name!r} is not in this room')

            if len(admins) == 0:
                raise PropertyValueIsInvalid(key, 'must be non-empty')

            room.admins = set(admins)

        elif key == 'min_players':
            if value < 1 or value > room.max_players:
                raise PropertyValueIsInvalid(key, 'must be at least 1 and at most `max_players`')
            room.min_players = value

        elif key == 'max_players':
            current_num_players = self._mapping.count_players_in_a_room(room_id)
            if value < current_num_players or value < room.min_players:
                raise PropertyValueIsInvalid(
                    key,
                    'must be at least the current number of players in the rooms and at least `min_players`'
                )
            room.max_players = value

        elif key == 'snake_len':
            if value < 1:
                raise PropertyValueIsInvalid(key, 'must be at least 1')
            room.snake_len = value

        elif key == 'field_width':
            if value < 2:
                raise PropertyValueIsInvalid(key, 'must be at least 2')
            room.field_width = value

        elif key == 'field_height':
            if value < 2:
                raise PropertyValueIsInvalid(key, 'must be at least 2')
            room.field_height = value

        elif key == 'num_food_items':
            if value < 0:
                raise PropertyValueIsInvalid(key, 'must be non-negative')
            room.num_food_items = value

        elif key == 'respawn_food':
            room.respawn_food = value

        elif key == 'open':
            room.open = value

        elif key == 'max_turns':
            if value < 1:
                raise PropertyValueIsInvalid(key, 'must be at least 1')
            room.max_turns = value

        elif key == 'turn_timeout_seconds':
            if not math.isfinite(value) or value <= 0:
                raise PropertyValueIsInvalid(key, 'must be finite, non-nan and non-negative')
            room.turn_timeout_seconds = value

        else:
            raise Exception(f'Invalid room property name: {key!r}')

    def list_players_in_a_room(self, room_name: str):
        room_id = self._alias_map[room_name]
        clients = self._mapping.list_clients_in_a_room(room_id)
        return [str(x) for x in clients if x.is_player()]

    async def wait_until_game_starts(
        self,
        invoking_client: ClientName,
    ) -> Tuple[Game, GameRoom]:
        # Precondition: client must be in a room, a game must not have started there,
        # and it is the first time this client reports being ready.
        self._mapping.check_that_client_is_not_in_hub(invoking_client)
        room_id = self._mapping.get_room_with_client(invoking_client)
        room = self._rooms[room_id]
        if room.game_started:
            raise Exception('The game in your room has already started')

        sync_object = self._room_sync[room_id]
        readiness_set = sync_object.readiness_set
        if invoking_client in readiness_set:
            raise Exception('You have already declared being ready')

        readiness_set.add(invoking_client)

        room_info = self._get_room_info_unchecked(invoking_client, room_id)
        clients = set(self._mapping.list_clients_in_a_room(room_id))
        num_players = sum(1 for x in clients if x.is_player())

        if num_players >= room_info.min_players and len(readiness_set) == len(clients):
            assert readiness_set == clients

            # Ready to start a game.

            # TODO: shuffle for fairness.
            client_names = list(clients)

            game = create_game(client_names, room.as_game_config())
            game_room = GameRoom(client_names, game, room_info.name)
            game_room.set_turn_timeout(room.turn_timeout_seconds)

            await sync_object.pubsub.publish((game, game_room))
            logger.info('The game in the room {!r} is starting', room.name)

            room.game_started = True

            async def coro() -> None:
                await game_room.run_loop()
                self.remove_room(room_info.name)

            await curio.spawn(coro, daemon=True)
        else:
            # Subscribe to receive the game and game_room objects when the game begins.
            game, game_room = await sync_object.pubsub.receive()

        return game, game_room

    def list_room_infos(self, invoking_client: ClientName) -> Iterable[RoomInfo]:
        for room_id in self._rooms.keys():
            yield self._get_room_info_unchecked(invoking_client, room_id)

    def _get_room_info_unchecked(self, invoking_client: ClientName, room_id: str) -> RoomInfo:
        room = self._rooms[room_id]

        if room.game_started:
            # TODO: maybe make an exception for viewers?
            can_join = 'no'
        elif (
            self._mapping.count_players_in_a_room(room_id) + (1 if invoking_client.is_player() else 0)
                > room.max_players
        ):
            can_join = 'no'
        else:
            can_join = room.open.match(
                open = lambda: 'yes',
                closed = lambda: 'no',
                whitelist = lambda whitelist: {False: 'no', True: 'yes'}[
                    invoking_client.is_player() and (str(invoking_client) in whitelist)
                ],
                password = lambda _: 'password',
            ) # type: ignore

        can_join = cast(str, can_join)

        return RoomInfo(
            id = room_id,
            name = room.name,
            min_players = room.min_players,
            max_players = room.max_players,
            players = [
                str(x)
                for x in self._mapping.list_clients_in_a_room(room_id)
                if x.is_player()
            ],
            can_join = can_join,
        )


def create_game(client_names: List[ClientName], game_config: GameConfig) -> Game:
    return Game(
        [str(x) for x in client_names if x.is_player()],
        game_config,
    )


def check_that_room_name_is_valid(room_name: str) -> None:
    if not is_room_name_valid(room_name):
        raise ValueError(f'Room name is invalid: {room_name!r}')


def is_room_name_valid(room_name: str) -> bool:
    return room_name.isprintable()
