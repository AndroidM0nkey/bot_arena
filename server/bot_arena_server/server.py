from bot_arena_server.game import Game

import re
from typing import Tuple, Callable, Coroutine, List

import curio    # type: ignore
from bot_arena_proto.session import ServerSession, ClientInfo
from loguru import logger


__all__ = [
    'Server',
]


def is_name_valid(name):
    return re.match(r'^[a-zA-Z0-9_-]+$', name) is not None


def create_game(client_infos) -> Game:
    field_width = 30
    field_height = 20
    return Game(field_width, field_height, [x.name for x in client_infos])


class Server:
    def __init__(
        self,
        client_handler: Callable[[ServerSession, ClientInfo, Game], Coroutine[None, None, None]],
    ):
        self._client_handler = client_handler
        self._client_infos: List[ClientInfo] = []
        self._game_pubsub = PublishSubscribeService()

    def listen(self, host: str, port: int) -> None:
        curio.run(curio.tcp_server, host, port, self._handle_client)

    async def _handle_client(self, socket: curio.io.Socket, peer_address: Tuple[str, int]):
        host, port = peer_address
        logger.info('Connection from {}:{}', host, port)
        stream = socket.as_stream()
        sess = ServerSession(stream)

        client_info = await sess.pre_initialize()
        if is_name_valid(client_info.name):
            logger.info('{} joined the party', client_info.name)
            await sess.initialize_ok()
        else:
            await sess.initialize_err('Invalid or unacceptable player name')
            return

        self._client_infos.append(client_info)
        if len(self._client_infos) >= self.CLIENTS_PER_GAME:
            logger.info('Creating a game room for {}', ', '.join(x.name for x in self._client_infos))
            client_infos = self._client_infos
            self._client_infos = []
            game = create_game(client_infos)
            await self._game_pubsub.publish(game)
        else:
            game = await self._wait_until_game_is_ready(sess)

        await sess.wait_until_ready()
        await sess.start_game(game.info())
        logger.info('Game with {} has started', client_info.name)
        await self._client_handler(sess, client_info, game)

    async def _wait_until_game_is_ready(self, sess: ServerSession) -> Game:
        # TODO: poll for messages from the client.
        return await self._game_pubsub.receive()

    # TODO: don't hardcode this.
    CLIENTS_PER_GAME = 2


class PublishSubscribeService:
    def __init__(self):
        self._queues = []

    async def publish(self, message):
        # Safe handling of potential re-subscribers
        queues = self._queues
        self._queues = []

        for q in queues:
            await q.put(message)

    def subscribe(self):
        q = curio.Queue(maxsize=1)
        self._queues.append(q)
        return q

    async def receive(self):
        q = self.subscribe()
        return await q.get()
