import itertools
import re

from adt import adt, Case
from bot_arena_proto.session import ClientInfo
from dataclasses import dataclass

@adt
class ClientType:
    PLAYER: Case
    VIEWER: Case


class ClientName:
    _valid_identifier_regex = re.compile(r'^[a-zA-Z0-9_-]+$')
    _counter = itertools.count()

    def __init__(self, raw_name: str) -> None:
        if ClientName._valid_identifier_regex.match(raw_name):
            self._name = raw_name
            self._type = ClientType.PLAYER()
        elif raw_name == '@viewer':
            self._name = str(next(self._counter))
            self._type = ClientType.VIEWER()
        else:
            raise ValueError(f'Invalid client name: {raw_name!r}')

    def __str__(self) -> str:
        return self._type.match(
            player = lambda: self._name,
            viewer = lambda: '@viewer:' + self._name,
        ) # type: ignore

    def __repr__(self) -> str:
        return self._type.match(
            player = lambda: f'[Player {self._name!r}]',
            viewer = lambda: f'[Viewer {self._name}]',
        ) # type: ignore

    def __eq__(self, other) -> bool:
        if not isinstance(other, ClientName):
            return False
        return str(self) == str(other)

    def __hash__(self) -> int:
        return 0x5eb1bc41c5767e01 ^ hash(str(self))

    def is_player(self) -> bool:
        return self._type.match(
            player = lambda: True,
            viewer = lambda: False,
        ) # type: ignore


@dataclass
class RichClientInfo:
    info: ClientInfo
    name: ClientName
