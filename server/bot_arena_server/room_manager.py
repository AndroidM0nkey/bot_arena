from bot_arena_server.room_mapping import RoomMapping
from bot_arena_proto.data import RoomOpenness, FoodRespawnBehavior

from dataclasses import dataclass
from typing import Dict, Set


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
    min_players: int
    max_players: int
    snake_len: int
    field_width: int
    field_height: int
    num_food_items: int
    respawn_food: FoodRespawnBehavior
    open: RoomOpenness


class RoomManager:
    def __init__(self):
        self._mapping = RoomMapping()
        self._rooms: Dict[str, RoomDetails] = {}

    # TODO
