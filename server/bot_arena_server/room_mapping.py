from typing import Dict, Set, Iterable


__all__ = [
    'RoomExistsError',
    'RoomDoesNotExistError',
    'PlayerInRoomError',
    'PlayerNotInRoomError',
    'RoomMapping',
]


class RoomExistsError(KeyError):
    def __init__(self, room_name: str) -> None:
        super().__init__(room_name)
        self._room_name = room_name

    def __repr__(self) -> str:
        return f'Room "{self._room_name}" already exists'


class RoomDoesNotExistError(KeyError):
    def __init__(self, room_name: str) -> None:
        super().__init__(room_name)
        self._room_name = room_name

    def __repr__(self) -> str:
        return f'Room "{self._room_name}" does not exist'


class PlayerInRoomError(KeyError):
    def __init__(self, room_name: str, player: str) -> None:
        super().__init__(room_name)
        self._room_name = room_name
        self._player = player

    def __repr__(self) -> str:
        return f'Player "{self._player}" is already in the room "{self._room_name}"'


class PlayerNotInRoomError(KeyError):
    def __init__(self, room_name: Optional[str], player: str) -> None:
        super().__init__(room_name)
        self._room_name = room_name
        self._player = player

    def __repr__(self) -> str:
        return f'Player "{self._player}" is not in ' + (
            'a room'
            if self._room_name is None else
            f'the room {self._room_name}'
        )


class RoomMapping:
    def __init__(self) -> None:
        self._players_to_rooms_map: Dict[str, str] = {}
        self._rooms_to_players_map: Dict[str, Set[str]] = {}

    def room_exists(self, room_name: str) -> bool:
        return room_name in self._rooms_to_players_map

    def add_room(self, room_name: str) -> None:
        if self.room_exists(room_name):
            raise RoomExistsError(room_name)

        self._rooms_to_players_map[room_name] = set()

    def remove_room(self, room_name: str) -> None:
        if not self.room_exists(room_name):
            raise RoomDoesNotExistError(room_name)

        for player in self._rooms_to_players_map[room_name]:
            self._players_to_rooms_map.pop(player, None)

        self._rooms_to_players_map.pop(room_name)

    def add_player_to_room(self, room_name: str, player: str) -> None:
        if not self.room_exists(room_name):
            raise RoomDoesNotExistError(room_name)

        self._check_that_player_is_in_hub(player)
        self._rooms_to_players_map[room_name].add(player)
        self._players_to_rooms_map[player] = room_name

    def remove_player_from_room(self, player: str) -> None:
        self._check_that_player_is_not_in_hub(player)
        room_name = self._players_to_rooms_map.pop(player)
        self._rooms_to_players_map[room_name].remove(player)

    def list_rooms(self) -> Iterable[str]:
        return self._rooms_to_players_map.keys()

    def list_players_in_a_room(self, room_name: str) -> Iterable[str]:
        if not self.room_exists(room_name):
            raise RoomDoesNotExistError(room_name)

        return self._rooms_to_players_map[room_name]

    def get_room_with_player(self, player: str) -> str:
        _check_that_player_is_not_in_hub(player)
        return self._players_to_rooms_map[player]

    def _check_that_player_is_in_hub(self, player: str) -> None:
        if player in self._players_to_rooms_map:
            raise PlayerInRoomError(self._players_to_rooms_map[player], player)

    def _check_that_player_is_not_in_hub(self, player: str) -> None:
        if player not in self._players_to_rooms_map:
            raise PlayerNotInRoomError(None, player)
