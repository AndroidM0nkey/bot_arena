from bot_arena_server.client_name import ClientName
from bot_arena_server.game import Game, GameScore
from bot_arena_server.pubsub import PublishSubscribeService

from dataclasses import dataclass
from typing import List, Dict, Callable, Coroutine, Any, Set, Optional

import curio    # type: ignore
from adt import adt, Case
from bot_arena_proto.event import Event
from bot_arena_proto.session import ServerSession
from loguru import logger # type: ignore


__all__ = [
    'GameRoom',
    'GameRoomError',
    'GameRoomExit',
]


class GameRoomExit(BaseException):
    pass


class GameRoomError(Exception):
    pass


class GameRoom:
    def __init__(self, client_names: List[ClientName], game: Game, name: str) -> None:
        self._pending_clients = {name: make_pending_client_context(name) for name in client_names}
        self._clients: Dict[ClientName, ClientContext] = {}
        self._client_names = client_names
        self._game = game
        self._game_end_pubsub: PublishSubscribeService[None] = PublishSubscribeService()
        self._name = name

    def get_score(self) -> GameScore:
        return self._game.get_score()

    def set_session(self, client_name: ClientName, session: ServerSession) -> None:
        if client_name in self._clients:
            raise GameRoomError(f'Session already added for {client_name!r}')
        if client_name not in self._pending_clients:
            raise GameRoomError(f'No such client in the game room: {client_name!r}')
        pending_context = self._pending_clients.pop(client_name)
        context = ClientContext(
            sync_queue = pending_context.sync_queue,
            session = session,
            category = pending_context.category,
        )
        self._clients[client_name] = context

    def mark_snake_dead(self, client_name: ClientName) -> None:
        assert client_name.is_player()
        self._check_for_client(client_name)
        context = self._clients[client_name]

        if context.category == ClientCategory.DEAD_PLAYER():
            raise GameRoomError(f'Snake {client_name!r} somehow managed to die twice')

        context.category = ClientCategory.DEAD_PLAYER()
        self._game.kill_snake_off(str(client_name))

    def mark_client_disconnected(self, client_name: ClientName) -> None:
        self._check_for_client(client_name)
        context = self._clients[client_name]

        if context.category == ClientCategory.DISCONNECTED():
            raise GameRoomError(f'Client {client_name!r} somehow managed to disconnect twice')

        if context.category == ClientCategory.ALIVE_PLAYER():
            self._game.kill_snake_off(str(client_name))

        context.category = ClientCategory.DISCONNECTED()

    async def report_death(self, client_name: ClientName) -> None:
        assert client_name.is_player()
        self._check_for_client(client_name)

        await self.broadcast_event(
            Event(name='SnakeDied', data=str(client_name), must_know=False),
            lambda name: True,
        )

    async def report_disconnect(self, client_name: ClientName) -> None:
        # We do not have a client-recognizable naming scheme for viewers,
        # so we do not tell clients anything about them.
        assert client_name.is_player()
        self._check_for_client(client_name)

        await self.broadcast_event(
            Event(name='ClientDisconnected', data=str(client_name), must_know=False),
            lambda name: True,
        )

    async def finish_turn(self, client_name: ClientName) -> None:
        assert client_name.is_player()
        self._check_for_client(client_name)

        queue = self._clients[client_name].sync_queue
        assert queue is not None
        await queue.task_done()

    async def wait_for_turn(self, client_name: ClientName) -> None:
        assert client_name.is_player()
        self._check_for_client(client_name)

        queue = self._clients[client_name].sync_queue
        assert queue is not None
        logger.debug('Waiting for a queue message ({!r})', client_name)
        msg = await queue.get()
        logger.debug('Got {!r} from queue ({!r})', msg, client_name)


        if msg == 'continue':
            # Return the control to the player coroutine.
            return
        elif msg == 'exit':
            # Raise a corresponding exception in the player coroutine.
            raise GameRoomExit()
        else:
            raise Exception(f'Internal error: unknown synchronization message: {msg!r}')

    async def run_loop(self) -> None:
        last_game_score = self.get_score()
        await self.broadcast_event(
            Event(name='GameScoreChanged', data=last_game_score.score, must_know=False),
            lambda _: True,
        )

        logger.debug('Loop started')
        while True:
            logger.debug('New round')
            for client_name in self._client_names:
                if self._game.is_finish_condition_satisfied():
                    logger.debug('Loop finished')
                    logger.info('Game in the room {!r} has finished', self.name)
                    await self.terminate_all_sessions()
                    await self._game_end_pubsub.publish(None)
                    return

                if self._clients[client_name].category != ClientCategory.ALIVE_PLAYER():
                    continue

                logger.debug('{!r}\'s turn', client_name)
                queue = self._clients[client_name].sync_queue
                assert queue is not None
                await queue.put('continue')
                await queue.join()

                current_game_score = self.get_score()
                logger.debug('Game score check: {} vs {}', last_game_score, current_game_score)
                if current_game_score != last_game_score:
                    logger.debug('New game score: {}', current_game_score)
                    await self.broadcast_event(
                        Event(name='GameScoreChanged', data=current_game_score.score, must_know=False),
                        lambda _: True,
                    )
                    last_game_score = current_game_score


    async def terminate_all_sessions(self) -> None:
        logger.debug('Terminating all game sessions in this game room')
        for client_name in self._client_names:
            if client_name.is_player():
                await self.terminate_session_for(client_name)

    async def terminate_session_for(self, client_name: ClientName) -> None:
        context = self._clients[client_name]
        if context.category == ClientCategory.DISCONNECTED():
            logger.debug('Session for {!r} is already dead', client_name)
            return

        assert client_name.is_player()
        logger.debug('Terminating session for {!r}', client_name)
        queue = context.sync_queue
        assert queue is not None
        await queue.put('exit')
        await queue.put(None)

    async def broadcast(
        self,
        action: Callable[[ServerSession], Coroutine[Any, None, None]],
        filter_func: Callable[[ClientName], bool],
    ) -> None:
        for client_name, context in self._clients.items():
            if context.category != ClientCategory.DISCONNECTED() and filter_func(client_name):
                logger.debug('Broadcast: {!r}, context = {!r}', client_name, context)
                await action(context.session)

    async def broadcast_event(self, event: Event, filter_func: Callable[[ClientName], bool]) -> None:
        logger.debug(f'Broadcasting event: {event}')

        async def callback(sess: ServerSession):
            await sess.send_event(event)

        await self.broadcast(callback, filter_func)

    async def wait_until_game_ends(self) -> None:
        await self._game_end_pubsub.receive()

    def _check_for_client(self, client_name: ClientName) -> None:
        if client_name not in self._clients:
            raise GameRoomError(f'No such client in the game room: {client_name!r}')

    @property
    def name(self) -> str:
        return self._name


@adt
class ClientCategory:
    ALIVE_PLAYER: Case
    DEAD_PLAYER: Case
    VIEWER: Case
    DISCONNECTED: Case


@dataclass
class PendingClientContext:
    sync_queue: Optional[curio.Queue]
    category: ClientCategory


@dataclass
class ClientContext:
    sync_queue: Optional[curio.Queue]
    session: ServerSession
    category: ClientCategory


def make_pending_client_context(client_name: ClientName):
    if client_name.is_player():
        return PendingClientContext(
            sync_queue = curio.Queue(maxsize=1),
            category = ClientCategory.ALIVE_PLAYER(),
        )
    else:
        return PendingClientContext(
            sync_queue = None,
            category = ClientCategory.VIEWER(),
        )
