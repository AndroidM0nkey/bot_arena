from bot_arena_server.client_name import ClientName, RichClientInfo
from bot_arena_server.game import Game
from bot_arena_server.game_room import GameRoom
from bot_arena_server.pubsub import PublishSubscribeService
from bot_arena_server.room_manager import RoomManager

from typing import Tuple, Callable, Coroutine, List, Optional, cast, Dict

import curio    # type: ignore
from adt import adt, Case
from bot_arena_proto.session import ServerSession, ClientInfo, AsyncStream
from loguru import logger # type: ignore


__all__ = [
    'Server',
]


@adt
class ClientWorkerState:
    HUB: Case
    ROOM: Case
    READY: Case
    GAME: Case[Game, GameRoom]


class ClientWorker:
    def __init__(self, client_info: RichClientInfo, server: 'Server', sess: ServerSession) -> None:
        self._client_info = client_info
        self._server = server
        self._sess = sess
        self._state = ClientWorkerState.HUB()
        self._should_terminate = False

    async def run(self) -> None:
        while self.should_run():
            await self.run_step()

    def should_run(self) -> bool:
        return not self._should_terminate

    async def run_step(self) -> None:
        try:
            await self._state.match(
                hub = self.run_hub_step,
                room = self.run_room_step,
                ready = self.run_ready_step,
                game = self.run_game_step,
            )
        except EOFError:
            self._state.match(
                hub = self.on_disconnect_from_hub,
                room = self.on_disconnect_from_room,
                ready = self.on_disconnect_from_ready,
                game = self.on_disconnect_from_game,
            )
            self._should_terminate = True

    def on_disconnect_from_hub(self) -> None:
        pass

    def on_disconnect_from_room(self) -> None:
        self._server._room_manager.handle_room_quit(self._client_info.name)
    
    def on_disconnect_from_ready(self) -> None:
        self._server._room_manager.handle_room_quit(self._client_info.name)

    def on_disconnect_from_game(self, *args) -> None:
        pass

    async def run_hub_step(self) -> None:
        msg = await self._sess.wait_for_hub_action()
        msg_type = msg.kind()
        client_name = self._client_info.name

        try:
            if msg_type == 'ListRooms':
                room_infos = list(self._server._room_manager.list_room_infos(client_name))
                await self._sess.respond_with_room_list(room_infos)
            elif msg_type == 'EnterRoom':
                room_name = msg.enter_room()
                self._server._room_manager.handle_room_entry(client_name, room_name)
                self._state = ClientWorkerState.ROOM()
                await self._sess.respond_ok()
            elif msg_type == 'NewRoom':
                self._server._room_manager.create_room(client_name)
                self._state = ClientWorkerState.ROOM()
                await self._sess.respond_ok()
            elif msg_type == 'EnterAnyRoom':
                room_infos = list(self._server._room_manager.list_room_infos(client_name))

                joined = False
                for info in room_infos:
                    if info.can_join == 'yes':
                        self._server._room_manager.handle_room_entry(client_name, info.name)
                        joined = True

                if not joined:
                    self._server._room_manager.create_room(client_name)
                
                self._state = ClientWorkerState.ROOM()
                await self._sess.respond_ok()

            else:
                raise Exception(f'Invalid hub action: {msg!r}')
        except Exception as e:
            await self._sess.respond_err(str(e))

    async def run_room_step(self) -> None:
        msg = await self._sess.wait_for_room_action()
        msg_type = msg.kind()
        client_name = self._client_info.name

        try:
            if msg_type == 'LeaveRoom':
                self._server._room_manager.handle_room_quit(client_name)
                self._state = ClientWorkerState.HUB()
                await self._sess.respond_ok()
            elif msg_type == 'GetRoomProperties':
                props = self._server._room_manager.get_room_properties(client_name)
                await self._sess.respond_with_room_properties(props)
            elif msg_type == 'SetRoomProperties':
                props = msg.set_room_properties()
                self._server._room_manager.set_room_properties(client_name, props)
                await self._sess.respond_ok()
            elif msg_type == 'Ready':
                self._state = ClientWorkerState.READY()
                await self._sess.respond_ok()
            else:
                raise Exception(f'Invalid room action: {msg!r}')
        except Exception as e:
            await self._sess.respond_err(str(e))

    async def run_ready_step(self) -> None:
        client_name = self._client_info.name
        game, game_room = await self._server._room_manager.wait_until_game_starts(client_name)
        self._state = ClientWorkerState.GAME(game, game_room)

    async def run_game_step(self, game: Game, game_room: GameRoom) -> None:
        await self._server._client_handler(self._sess, self._client_info, game, game_room)
        self._state = ClientWorkerState.HUB()


class Server:
    def __init__(
        self,
        client_handler: Callable[
            [ServerSession, RichClientInfo, Game, GameRoom],
            Coroutine[None, None, None],
        ],
    ) -> None:
        self._client_handler = client_handler
        self._client_infos: Dict[ClientName, RichClientInfo] = {}
        self._game_pubsub: PublishSubscribeService[Tuple[Game, GameRoom]] = PublishSubscribeService()
        self._room_manager = RoomManager()

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
        assert client_name not in self._client_infos
        self._client_infos[client_name] = client_rich_info

        try:
            worker = ClientWorker(client_rich_info, self, sess)
            await worker.run()

        finally:
            self._client_infos.pop(client_name)

    async def _wait_until_game_is_ready(self, sess: ServerSession) -> Tuple[Game, GameRoom]:
        # TODO: poll for messages from the client.
        return await self._game_pubsub.receive()

    # TODO: don't hardcode this.
    CLIENTS_PER_GAME = 3
