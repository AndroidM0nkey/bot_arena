# (yet another library that does not care about the benefits static typing brings)
import curio    # type: ignore
from typing import Tuple, Callable, Coroutine

from bot_arena_proto.session import ServerSession


__all__ = [
    'Server',
]


class Server:
    def __init__(self, client_handler: Callable[[ServerSession], Coroutine[None, None, None]]):
        self._client_handler = client_handler

    def listen(self, host: str, port: int) -> None:
        curio.run(curio.tcp_server, host, port, self._handle_client)

    async def _handle_client(self, socket: curio.io.Socket, peer_address: Tuple[str, int]):
        host, port = peer_address
        print(f'Connection from {host}:{port}')
        stream = socket.as_stream()
        sess = ServerSession(stream)
        await self._client_handler(sess)
