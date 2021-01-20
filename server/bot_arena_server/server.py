from bot_arena_server.game import Game

# (yet another library that does not care about the benefits static typing brings)
import curio    # type: ignore
from typing import Tuple, Callable, Coroutine

from bot_arena_proto.session import ServerSession
from loguru import logger


__all__ = [
    'Server',
]


class Server:
    def __init__(self, client_handler: Callable[[ServerSession, Game], Coroutine[None, None, None]]):
        self._client_handler = client_handler

    def listen(self, host: str, port: int) -> None:
        curio.run(curio.tcp_server, host, port, self._handle_client)

    async def _handle_client(self, socket: curio.io.Socket, peer_address: Tuple[str, int]):
        host, port = peer_address
        logger.info('Connection from {}:{}', host, port)
        stream = socket.as_stream()
        sess = ServerSession(stream)

        # TODO: allocate game rooms properly, not one per client.
        # (this is a stub as for now).
        game = Game(field_width=30, field_height=20, snake_names=['Player'])

        await self._client_handler(sess, game)
