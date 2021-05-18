from dataclasses import dataclass
from typing import Optional

from bot_arena_proto.data import FoodRespawnBehavior


@dataclass
class GameConfig:
    snake_len: int
    field_width: int
    field_height: int
    num_food_items: int
    respawn_food: FoodRespawnBehavior
    max_turns: Optional[int]
