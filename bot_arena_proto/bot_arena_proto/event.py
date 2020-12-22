from bot_arena_proto.serialization import Primitive, DeserializationAdtTagError, ensure_type

from dataclasses import dataclass
from typing import Type, cast

from adt import adt, Case


@adt
class Event:
    """An event that is reported to a client.

    Currently, the following types of events exist:

    - SNAKE_DIED:       A snake with the specified name has died.

    - GAME_FINISHED:    The game has just finished.

    - GAME_STARTED:     The game has just started. The two parameters
                        are the width and the height of the game field.
    """

    SNAKE_DIED: Case[str]
    GAME_FINISHED: Case
    GAME_STARTED: Case[int, int]

    def to_primitive(self) -> Primitive:
        return cast(
            Primitive,
            self.match(
                snake_died = lambda snake_name: ['SnakeDied', {'name': snake_name}],
                game_finished = lambda: ['GameFinished'],
                game_started = lambda width, height: ['GameStarted', {'width': width, 'height': height}],
            )
        )

    @classmethod
    def from_primitive(Class: Type['Event'], p: Primitive) -> 'Event':
        p = ensure_type(p, list)
        [tag, *data] = p
        tag = ensure_type(tag, str)
        if tag == 'SnakeDied':
            [data_dict] = data
            data_dict = ensure_type(data_dict, dict)
            snake_name = ensure_type(data_dict['name'], str)
            return Event.SNAKE_DIED(snake_name)
        if tag == 'GameFinished':
            return Event.GAME_FINISHED()
        if tag == 'GameStarted':
            [data_dict] = data
            data_dict = ensure_type(data_dict, dict)
            width = ensure_type(data_dict['width'], int)
            height = ensure_type(data_dict['height'], int)
            return Event.GAME_STARTED(width, height)

        raise DeserializationAdtTagError(Class, tag)
