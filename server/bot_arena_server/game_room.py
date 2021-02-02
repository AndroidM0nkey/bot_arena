from bot_arena_server.game import Game

from typing import List

import curio    # type: ignore
from loguru import logger


__all__ = [
    'GameRoom'
]


class GameRoom:
    def __init__(self, client_names: List[str]) -> None:
        self._clients = {name: curio.Queue(maxsize=1) for name in client_names}
        self._client_names = client_names
        self._took_turn = {name: False for name in client_names}

    async def wait_for_turn(self, client_name: str) -> None:
        if client_name not in self._clients:
            raise KeyError(f'No such client in the game room: `{client_name}`')

        logger.debug('id(self) = {}', id(self))
        logger.debug('A {}', client_name)
        queue = self._clients[client_name]
        if self._took_turn[client_name]:
            logger.debug('B {}', client_name)
            await queue.task_done()
        logger.debug('C {}', client_name)
        self._took_turn[client_name] = True
        await queue.get()
        logger.debug('D {}', client_name)

    async def run_loop(self) -> None:
        logger.debug('Loop started')
        while True:
            logger.debug('New round')
            for client_name in self._client_names:
                # TODO: don't accept turns from dead players
                logger.debug('{}\'s turn', client_name)
                queue = self._clients[client_name]
                await queue.put(None)
                logger.debug('here')
                await queue.join()
        logger.debug('Loop finished')
