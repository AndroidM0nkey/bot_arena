from bot_arena_server.client_name import ClientName, RichClientInfo
from bot_arena_server.game import Game
from bot_arena_server.game_room import GameRoom
from bot_arena_server.pubsub import PublishSubscribeService

from typing import Tuple, Callable, Coroutine, List, Optional

import curio    # type: ignore
from bot_arena_proto.session import ServerSession, ClientInfo, AsyncStream
from loguru import logger # type: ignore


__all__ = [
    'Server',
]


def create_game(client_infos: List[RichClientInfo]) -> Game:
    field_width = 30
    field_height = 20
    return Game(
        field_width,
        field_height,
        [str(x.name) for x in client_infos if x.name.is_player()],
    )


class Server:
    def __init__(
        self,
        client_handler: Callable[
            [ServerSession, RichClientInfo, Game, GameRoom],
            Coroutine[None, None, None],
        ],
    ) -> None:
        self._client_handler = client_handler
        self._client_rich_infos: List[RichClientInfo] = []
        self._game_pubsub: PublishSubscribeService[Tuple[Game, GameRoom]] = PublishSubscribeService()

    def listen(self, host: str, port: int) -> None:
        logger.info('Listening on {}:{}', host, port)
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
        try:
            client_name = ClientName(client_info.name)
            logger.info('{!r} joined the party', client_name)
            await sess.initialize_ok()
        except Exception as e:
            await sess.initialize_err(str(e))
            return

        client_rich_info = RichClientInfo(info=client_info, name=client_name)
        self._client_rich_infos.append(client_rich_info)
        if len(self._client_rich_infos) >= self.CLIENTS_PER_GAME:
            logger.info(
                'Creating a game room for {}',
                ', '.join(repr(x.name) for x in self._client_rich_infos),
            )
            client_rich_infos = self._client_rich_infos
            self._client_rich_infos = []
            game = create_game(client_rich_infos)
            game_room = GameRoom([info.name for info in client_rich_infos])
            await self._game_pubsub.publish((game, game_room))
            is_game_creator = True
        else:
            game, game_room = await self._wait_until_game_is_ready(sess)
            is_game_creator = False

        if is_game_creator:
            await curio.spawn(game_room.run_loop)

        await sess.wait_until_ready()
        await sess.start_game(game.info())
        logger.info('Game with {!r} has started', client_name)
        await self._client_handler(sess, client_rich_info, game, game_room)

    async def _wait_until_game_is_ready(self, sess: ServerSession) -> Tuple[Game, GameRoom]:
        # TODO: poll for messages from the client.
        return await self._game_pubsub.receive()

    # TODO: don't hardcode this.
    CLIENTS_PER_GAME = 3
