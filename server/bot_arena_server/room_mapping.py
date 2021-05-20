from bot_arena_server.client_name import ClientName

from typing import Dict, Set, Iterable, Optional


__all__ = [
    'RoomExistsError',
    'RoomDoesNotExistError',
    'ClientInRoomError',
    'ClientNotInRoomError',
    'RoomMapping',
]


class RoomExistsError(KeyError):
    def __init__(self, room_name: str) -> None:
        super().__init__(room_name)
        self._room_name = room_name

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return f'Room {self._room_name!r} already exists'


class RoomDoesNotExistError(KeyError):
    def __init__(self, room_name: str) -> None:
        super().__init__(room_name)
        self._room_name = room_name

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return f'Room {self._room_name!r} does not exist'


class ClientInRoomError(KeyError):
    def __init__(self, room_name: str, client: ClientName) -> None:
        super().__init__(room_name)
        self._room_name = room_name
        self._client = client

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return f'{self._client!r} is already in the room {self._room_name!r}'


class ClientNotInRoomError(KeyError):
    def __init__(self, room_name: Optional[str], client: ClientName) -> None:
        super().__init__(room_name)
        self._room_name = room_name
        self._client = client

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return f'{self._client!r} is not in ' + (
            'a room'
            if self._room_name is None else
            f'the room {self._room_name!r}'
        )


class RoomMapping:
    def __init__(self) -> None:
        self._clients_to_rooms_map: Dict[ClientName, str] = {}
        self._rooms_to_clients_map: Dict[str, Set[ClientName]] = {}

    def room_exists(self, room_name: str) -> bool:
        return room_name in self._rooms_to_clients_map

    def add_room(self, room_name: str) -> None:
        self.check_that_room_does_not_exist(room_name)
        self._rooms_to_clients_map[room_name] = set()

    def remove_room(self, room_name: str) -> None:
        self.check_that_room_exists(room_name)

        for client in self._rooms_to_clients_map[room_name]:
            self._clients_to_rooms_map.pop(client, None)

        self._rooms_to_clients_map.pop(room_name)

    def add_client_to_room(self, room_name: str, client: ClientName) -> None:
        self.check_that_room_exists(room_name)
        self.check_that_client_is_in_hub(client)

        self._rooms_to_clients_map[room_name].add(client)
        self._clients_to_rooms_map[client] = room_name

    def remove_client_from_room(self, client: ClientName) -> None:
        self.check_that_client_is_not_in_hub(client)
        room_name = self._clients_to_rooms_map.pop(client)
        self._rooms_to_clients_map[room_name].remove(client)

    def list_rooms(self) -> Iterable[str]:
        return self._rooms_to_clients_map.keys()

    def list_clients_in_a_room(self, room_name: str) -> Iterable[ClientName]:
        self.check_that_room_exists(room_name)
        return self._rooms_to_clients_map[room_name]

    def count_players_in_a_room(self, room_name: str) -> int:
        return sum(1 for name in self.list_clients_in_a_room(room_name) if name.is_player())

    def get_room_with_client(self, client: ClientName) -> str:
        self.check_that_client_is_not_in_hub(client)
        return self._clients_to_rooms_map[client]

    def check_that_client_is_in_hub(self, client: ClientName) -> None:
        if client in self._clients_to_rooms_map:
            raise ClientInRoomError(self._clients_to_rooms_map[client], client)

    def check_that_client_is_not_in_hub(self, client: ClientName) -> None:
        if client not in self._clients_to_rooms_map:
            raise ClientNotInRoomError(None, client)

    def check_that_room_exists(self, room_name: str) -> None:
        if not self.room_exists(room_name):
            raise RoomDoesNotExistError(room_name)

    def check_that_room_does_not_exist(self, room_name: str) -> None:
        if self.room_exists(room_name):
            raise RoomExistsError(room_name)
