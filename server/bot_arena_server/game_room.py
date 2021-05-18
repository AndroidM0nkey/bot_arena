from bot_arena_server.client_name import ClientName
from bot_arena_server.game import Game
from bot_arena_server.pubsub import PublishSubscribeService

from typing import List, Dict, Callable, Coroutine, Any, Set

import curio    # type: ignore
from adt import adt, Case
from bot_arena_proto.event import Event
from bot_arena_proto.session import ServerSession
from loguru import logger # type: ignore


__all__ = [
    'GameRoom',
    'GameRoomExit',
]


class GameRoomExit(BaseException):
    pass


class GameRoom:
    def __init__(self, client_names: List[ClientName], game: Game) -> None:
        # TODO: maybe transform this kind of storage into a dict of structures
        self._players = {name: curio.Queue(maxsize=1) for name in client_names if name.is_player()}
        self._client_names = client_names
        self._took_turn = {name: False for name in client_names}
        self._sessions: Dict[ClientName, ServerSession] = {}
        self._dead: Set[ClientName] = set()
        self._game = game
        self._game_end_pubsub: PublishSubscribeService[None] = PublishSubscribeService()

    def set_session(self, client_name: ClientName, session: ServerSession) -> None:
        if client_name in self._sessions:
            raise KeyError(f'Session already added for {client_name!r}')
        if client_name.is_player() and client_name not in self._players:
            raise KeyError(f'No such player in the game room: {client_name!r}')
        self._sessions[client_name] = session

    def mark_snake_dead(self, client_name: ClientName) -> None:
        assert client_name.is_player()
        if client_name in self._dead:
            raise KeyError(f'Snake {client_name!r} somehow managed to die twice')
        self._dead.add(client_name)
        self._game.kill_snake_off(str(client_name))

    async def report_death(self, client_name: ClientName) -> None:
        assert client_name.is_player()

        if client_name not in self._players:
            raise KeyError(f'No such player in the game room: {client_name!r}')

        await self.broadcast_event(
            Event(name='SnakeDied', data=str(client_name), must_know=False),
            lambda name: True,
        )

    async def finish_turn(self, client_name: ClientName) -> None:
        assert client_name.is_player()

        if client_name not in self._players:
            raise KeyError(f'No such player in the game room: {client_name!r}')

        queue = self._players[client_name]
        if self._took_turn[client_name]:
            await queue.task_done()
        self._took_turn[client_name] = True

    async def wait_for_turn(self, client_name: ClientName) -> None:
        assert client_name.is_player()

        if client_name not in self._players:
            raise KeyError(f'No such player in the game room: {client_name!r}')

        queue = self._players[client_name]
        if self._took_turn[client_name]:
            await queue.task_done()
        self._took_turn[client_name] = True
        msg = await queue.get()

        if msg == 'continue':
            # Return the control to the player coroutine.
            return
        elif msg == 'exit':
            # Raise a corresponding exception in the player coroutine.
            raise GameRoomExit()
        else:
            raise Exception(f'Internal error: unknown synchronization message: {msg!r}')

    async def run_loop(self) -> None:
        logger.debug('Loop started')
        while True:
            logger.debug('New round')
            for client_name in self._client_names:
                if self._game.is_finish_condition_satisfied():
                    logger.debug('Loop finished')
                    logger.info('Game between {} has finished', ', '.join(map(repr, self._players.keys())))
                    await self.terminate_all_sessions()
                    await self._game_end_pubsub.publish(None)
                    return

                if client_name in self._dead or not client_name.is_player():
                    continue

                logger.debug('{!r}\'s turn', client_name)
                queue = self._players[client_name]
                await queue.put('continue')
                await queue.join()

    async def terminate_all_sessions(self) -> None:
        logger.debug('Terminating all game sessions in this game room')
        for client_name in self._client_names:
            if client_name.is_player():
                await self.terminate_session_for(client_name)

    async def terminate_session_for(self, client_name: ClientName) -> None:
        assert client_name.is_player()
        queue = self._players[client_name]
        await queue.put('exit')

    async def broadcast(
        self,
        action: Callable[[ServerSession], Coroutine[Any, None, None]],
        filter_func: Callable[[ClientName], bool],
    ) -> None:
        for client_name, sess in self._sessions.items():
            if (client_name not in self._dead) and filter_func(client_name):
                await action(sess)

    async def broadcast_event(self, event: Event, filter_func: Callable[[ClientName], bool]) -> None:
        logger.debug(f'Broadcasting event: {event}')

        async def callback(sess: ServerSession):
            try:
                await sess.send_event(event)
            except BrokenPipeError:
                logger.warning('Broken pipe error')

        await self.broadcast(callback, filter_func)

    async def wait_until_game_ends(self) -> None:
        await self._game_end_pubsub.receive()
