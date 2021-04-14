from bot_arena_server.client_name import ClientName
from bot_arena_server.game import Game

from typing import List, Dict, Callable, Coroutine, Any, Set

import curio    # type: ignore
from adt import adt, Case
from bot_arena_proto.event import Event
from bot_arena_proto.session import ServerSession
from loguru import logger # type: ignore


__all__ = [
    'GameRoom'
]


class GameRoom:
    def __init__(self, client_names: List[ClientName]) -> None:
        # TODO: maybe transform this kind of storage into a dict of structures
        self._players = {name: curio.Queue(maxsize=1) for name in client_names if name.is_player()}
        self._client_names = client_names
        self._took_turn = {name: False for name in client_names}
        self._sessions: Dict[ClientName, ServerSession] = {}
        self._dead: Set[ClientName] = set()

    def set_session(self, client_name: ClientName, session: ServerSession) -> None:
        if client_name in self._sessions:
            raise KeyError(f'Session already added for {client_name!r}')
        if client_name.is_player() and client_name not in self._players:
            raise KeyError(f'No such player in the game room: {client_name!r}')
        self._sessions[client_name] = session

    async def report_death(self, client_name: ClientName) -> None:
        assert client_name.is_player()

        if client_name in self._dead:
            raise KeyError(f'Snake {client_name!r} somehow managed to die twice')
        if client_name not in self._players:
            raise KeyError(f'No such player in the game room: {client_name!r}')

        await self.broadcast_event(Event.SNAKE_DIED(str(client_name)), lambda name: True)
        self._dead.add(client_name)

    async def wait_for_turn(self, client_name: ClientName) -> None:
        assert client_name.is_player()

        if client_name not in self._players:
            raise KeyError(f'No such player in the game room: {client_name!r}')

        queue = self._players[client_name]
        if self._took_turn[client_name]:
            await queue.task_done()
        self._took_turn[client_name] = True
        await queue.get()

    async def run_loop(self) -> None:
        logger.debug('Loop started')
        while True:
            logger.debug('New round')
            for client_name in self._client_names:
                if client_name in self._dead or not client_name.is_player():
                    continue
                logger.debug('{}\'s turn', client_name)
                queue = self._players[client_name]
                await queue.put(None)
                await queue.join()
                # TODO: recognize the end of the game
        logger.debug('Loop finished')

    async def broadcast(
        self,
        action: Callable[[ServerSession], Coroutine[Any, None, None]],
        filter_func: Callable[[ClientName], bool],
    ) -> None:
        for client_name, sess in self._sessions.items():
            if filter_func(client_name):
                await action(sess)

    async def broadcast_event(self, event: Event, filter_func: Callable[[ClientName], bool]) -> None:
        logger.debug(f'Broadcasting event: {event}')
        await self.broadcast(lambda sess: sess.send_event(event), filter_func)
