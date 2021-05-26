from bot_arena_server.work_limit import WorkLimit

from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Protocol, Any


_T = TypeVar('_T', int, float)


class OptionalUpperBound(Generic[_T]):
    def __init__(self, bound: Optional[_T]) -> None:
        self._bound: Optional[_T] = bound

    def __contains__(self, value: Optional[_T]) -> bool:
        if value is None:
            return self._bound is None

        return (self._bound is None) or (value <= self._bound)

    def clamp(self, value: Optional[_T]) -> Optional[_T]:
        if value is None:
            return self._bound

        if self._bound is None:
            return value

        return min(self._bound, value)


class UpperBound(Generic[_T]):
    def __init__(self, bound: _T) -> None:
        self._bound: _T = bound

    def __contains__(self, value: _T) -> bool:
        return value <= self._bound

    def clamp(self, value: _T) -> _T:
        return min(value, self._bound)


class Range(Generic[_T]):
    def __init__(self, lower_bound: _T, upper_bound: _T) -> None:
        if upper_bound < lower_bound:
            raise ValueError('Invalid range: [{lower_bound}, {upper_bound}]')
        self._lower_bound: _T = lower_bound
        self._upper_bound: _T = upper_bound

    def __contains__(self, value: _T) -> bool:
        return self._lower_bound <= value <= self._upper_bound

    def clamp(self, value: _T) -> _T:
        return min(self._upper_bound, max(self._lower_bound, value))


@dataclass
class Limits:
    field_side_limits: Range[int]
    max_client_name_len: UpperBound[int]
    max_food_items: UpperBound[int]
    max_password_len: UpperBound[int]
    max_players_in_a_room: UpperBound[int]
    max_room_name_len: UpperBound[int]
    max_snake_len: UpperBound[int]
    max_turn_timeout: OptionalUpperBound[float]
    max_turns: OptionalUpperBound[int]
    work_units: WorkLimit
    turn_delay: float
