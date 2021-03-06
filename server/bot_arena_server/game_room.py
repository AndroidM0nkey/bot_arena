from bot_arena_server.client_name import ClientName
from bot_arena_server.control_flow import EnsureDisconnect
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


async def sleep_forever():
    while True:
        await curio.sleep(999999)


class GameRoomExit(BaseException):
    pass


class GameRoomError(Exception):
    pass


class GameRoom:
    def __init__(self, client_names: List[ClientName], game: Game, name: str, turn_delay: float) -> None:
        self._pending_clients = {name: make_pending_client_context(name) for name in client_names}
        self._clients: Dict[ClientName, ClientContext] = {}
        self._client_names = client_names
        self._game = game
        self._turn_timeout_seconds: Optional[float] = None
        self._name = name
        self._turn_delay = turn_delay

    def set_turn_timeout(self, turn_timeout_seconds: Optional[float]) -> None:
        self._turn_timeout_seconds = turn_timeout_seconds

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
            event_queue = LockedEventQueue(),
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

        await queue.task_done()

    async def wait_for_turn(self, client_name: ClientName) -> None:
        assert client_name.is_player()
        self._check_for_client(client_name)

        queue = self._clients[client_name].sync_queue

        logger.debug('Waiting for a queue message ({!r})', client_name)
        msg = await queue.get()
        logger.debug('Got {!r} from queue ({!r})', msg, client_name)


        if msg == 'continue':
            # Return the control to the player coroutine.
            return
        elif msg == 'exit':
            # Raise a corresponding exception in the player coroutine.
            raise GameRoomExit()
        elif msg == 'disconnect':
            # Ensure that the client disconnects immediately
            raise EnsureDisconnect()
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
                    await self._flush_event_queues()
                    logger.debug('Loop finished')
                    logger.info(
                        'Game in the room {!r} has finished (winners: {!r})',
                        self.name,
                        self._game.get_winners(),
                    )
                    await self.terminate_all_sessions()

                    return

                await self._flush_event_queues()

                if self._clients[client_name].category != ClientCategory.ALIVE_PLAYER():
                    continue

                logger.debug('{!r}\'s turn', client_name)
                queue = self._clients[client_name].sync_queue

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

                await curio.sleep(self._turn_delay)
            self._game.finish_turn()

    async def _flush_event_queues(self) -> None:
        for context in self._clients.values():
            events = context.event_queue.try_flush()
            try:
                for event in events:
                    await context.session.send_event(event)
            except (IOError, EOFError, OSError) as _:
                pass

    async def terminate_all_sessions(self) -> None:
        logger.debug('Terminating all game sessions in this game room')
        for client_name in self._client_names:

            await self.terminate_session_for(client_name)

    async def terminate_session_for(self, client_name: ClientName) -> None:
        context = self._clients[client_name]
        if context.category == ClientCategory.DISCONNECTED():
            logger.debug('Session for {!r} is already dead', client_name)
            return


        logger.debug('Terminating session for {!r}', client_name)
        queue = context.sync_queue

        await queue.put('exit')
        await queue.put(None)

    async def broadcast(
        self,
        action: Callable[['ClientContext'], Coroutine[Any, None, None]],
        filter_func: Callable[[ClientName], bool],
    ) -> None:
        for client_name, context in self._clients.items():
            if context.category != ClientCategory.DISCONNECTED() and filter_func(client_name):
                logger.debug('Broadcast: {!r}, context = {!r}', client_name, context)
                try:
                    await action(context)
                except (IOError, EOFError, OSError) as e:
                    logger.debug('Broadcast failed: endpoint disconnected')
                    await self.ensure_disconnect(client_name)

    async def ensure_disconnect(self, client_name: ClientName) -> None:
        logger.debug('Ensuring that {!r} is disconnected', client_name)
        queue = self._clients[client_name].sync_queue
        await queue.put('disconnect')
        await queue.put(None)

    async def broadcast_event(self, event: Event, filter_func: Callable[[ClientName], bool]) -> None:
        logger.debug(f'Broadcasting event: {event}')

        async def callback(context: ClientContext):
            context.event_queue.enqueue(event)

        await self.broadcast(callback, filter_func)

    async def wait_until_game_ends(self, client_name: ClientName) -> None:
        if client_name.is_player():
            raise NotImplementedError('GameRoom.wait_until_game_starts is only implemented for viewers')

        def raise_ensure_disconnect():
            raise EnsureDisconnect()

        def nop():
            pass

        notification = await self.wait_for_viewer_notification(client_name)
        notification.match(
            game_finished = nop,
            ensure_disconnect = raise_ensure_disconnect,
        )

    async def wait_for_viewer_notification(self, client_name: ClientName) -> 'ViewerNotification':
        queue = self._clients[client_name].sync_queue
        msg = await queue.get()
        if msg == 'exit':
            return ViewerNotification.GAME_FINISHED()
        if msg == 'disconnect':
            return ViewerNotification.ENSURE_DISCONNECT()

        raise Exception(f'Internal error: invalid viewer sync_queue message: {msg!r}')

    def _check_for_client(self, client_name: ClientName) -> None:
        if client_name not in self._clients:
            raise GameRoomError(f'No such client in the game room: {client_name!r}')

    @property
    def name(self) -> str:
        return self._name

    def lock_events_for(self, client_name: ClientName) -> 'EventLock':
        self._check_for_client(client_name)
        context = self._clients[client_name]
        return EventLock(context.event_queue)

    async def wait_for_turn_timeout(self, client_name: ClientName) -> None:
        assert client_name.is_player()

        if self._turn_timeout_seconds is None:
            await sleep_forever()
        else:
            await curio.sleep(self._turn_timeout_seconds)

        # TODO: maybe allow the player to stay in a viewer mode.
        logger.debug('Waiting for the client\'s action timed out')
        await self.broadcast_event(
            Event('PlayerTimedOut', str(client_name), must_know=False),
            lambda name: name != client_name,
        )
        raise EnsureDisconnect()


class LockedEventQueue:
    def __init__(self) -> None:
        self.queue: List[Event] = []
        self.is_locked = False

    def lock(self) -> None:
        assert not self.is_locked
        self.is_locked = True

    def unlock(self) -> None:
        assert self.is_locked
        self.is_locked = False

    def try_flush(self) -> List[Event]:
        if self.is_locked:
            return []
        else:
            queue = self.queue
            self.queue = []
            return queue

    def enqueue(self, event: Event) -> None:
        self.queue.append(event)


class EventLock:
    def __init__(self, locked_queue: LockedEventQueue) -> None:
        self.locked_queue = locked_queue

    def __enter__(self) -> None:
        self.locked_queue.lock()

    def __exit__(self, *args) -> None:
        self.locked_queue.unlock()


@adt
class ViewerNotification:
    GAME_FINISHED: Case
    ENSURE_DISCONNECT: Case


@adt
class ClientCategory:
    ALIVE_PLAYER: Case
    DEAD_PLAYER: Case
    VIEWER: Case
    DISCONNECTED: Case


@dataclass
class PendingClientContext:
    sync_queue: curio.Queue
    category: ClientCategory


@dataclass
class ClientContext:
    sync_queue: curio.Queue
    session: ServerSession
    category: ClientCategory
    event_queue: LockedEventQueue


def make_pending_client_context(client_name: ClientName) -> PendingClientContext:
    if client_name.is_player():
        return PendingClientContext(
            sync_queue = curio.Queue(maxsize=1),
            category = ClientCategory.ALIVE_PLAYER(),
        )
    else:
        return PendingClientContext(
            sync_queue = curio.Queue(maxsize=1),
            category = ClientCategory.VIEWER(),
        )
