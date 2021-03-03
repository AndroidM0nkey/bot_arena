from bot_arena_server.game import Game
from bot_arena_server.game_room import GameRoom
from bot_arena_server.pubsub import PublishSubscribeService

import re
from typing import Tuple, Callable, Coroutine, List

import curio    # type: ignore
from bot_arena_proto.session import ServerSession, ClientInfo, AsyncStream
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
        client_handler: Callable[
            [ServerSession, ClientInfo, Game, GameRoom],
            Coroutine[None, None, None],
        ],
    ) -> None:
        self._client_handler = client_handler
        self._client_infos: List[ClientInfo] = []
        self._game_pubsub: PublishSubscribeService[Tuple[Game, GameRoom]] = PublishSubscribeService()

    def listen(self, host: str, port: int) -> None:
        curio.run(curio.tcp_server, host, port, self._handle_client)

    async def _handle_client(
        self,
        socket: curio.io.Socket,
        peer_address: Tuple[str, int],
    ) -> None:
        host, port = peer_address
        logger.info('Connection from {}:{}', host, port)
        stream = socket.as_stream()
        await self._handle_client_with_stream(stream)


    async def _handle_client_with_stream(self, stream: AsyncStream) -> None:
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
            game_room = GameRoom(list(game.snake_names()))
            await self._game_pubsub.publish((game, game_room))
            is_game_creator = True
        else:
            game, game_room = await self._wait_until_game_is_ready(sess)
            is_game_creator = False

        if is_game_creator:
            await curio.spawn(game_room.run_loop)

        await sess.wait_until_ready()
        await sess.start_game(game.info())
        logger.info('Game with {} has started', client_info.name)
        await self._client_handler(sess, client_info, game, game_room)

    async def _wait_until_game_is_ready(self, sess: ServerSession) -> Tuple[Game, GameRoom]:
        # TODO: poll for messages from the client.
        return await self._game_pubsub.receive()

    # TODO: don't hardcode this.
    CLIENTS_PER_GAME = 2
