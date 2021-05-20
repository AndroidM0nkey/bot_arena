from bot_arena_server.client_name import RichClientInfo
from bot_arena_server.control_flow import EnsureDisconnect
from bot_arena_server.coroutine_utils import select
from bot_arena_server.game import Game, IllegalAction
from bot_arena_server.game_room import GameRoom, GameRoomExit

from dataclasses import dataclass
from typing import NoReturn

import curio # type: ignore
from bot_arena_proto.event import Event
from bot_arena_proto.session import ServerSession, GameInfo, ClientInfo
from loguru import logger # type: ignore


__all__ = [
    'run_game_loop',
]


async def run_game_loop(
    sess: ServerSession,
    client_info: RichClientInfo,
    game: Game,
    game_room: GameRoom,
) -> None:
    game_loop = GameLoop(sess, client_info, game, game_room)
    await game_loop.run()


@dataclass
class GameLoop:
    sess: ServerSession
    client_info: RichClientInfo
    game: Game
    game_room: GameRoom

    async def run(self) -> None:
        try:
            self.game_room.set_session(self.client_info.name, self.sess)
            await self.sess.send_event(
                Event(name='GameStarted', data=self.game.info().to_primitive(), must_know=True)
            )
            await self.sess.send_new_field_state(self.game.field.get_state())

            if self.client_info.name.is_player():
                await self.run_for_player()
            else:
                await self.run_for_non_player()
        except BaseException as e:
            if not isinstance(e, (EOFError, IOError)):
                logger.error('{!r} disconnected because of an exception: {}', self.client_info.name, e)
            await self.on_disconnect()
            raise EnsureDisconnect(e)

    async def run_for_non_player(self) -> None:
        while True:
            which, _ = await select(
                message = self.sess.recv_message(),
                end = self.game_room.wait_until_game_ends(self.client_info.name),
            )

            if which == 'message':
                await self.sess.respond_err('You cannot send messages during a game')
                continue

            break

        winners = self.game.get_winners()
        await self.sess.send_event(Event(
            name = 'GameFinished',
            data = {'winners': winners},
            must_know = True,
        ))

    async def run_for_player(self) -> None:
        client_name = self.client_info.name

        while True:
            try:
                which, _ = await select(
                    message = self.sess.recv_message(),
                    turn = self.game_room.wait_for_turn(client_name),
                )

                if which == 'message':
                    await self.sess.respond_err('It is not your turn')
                    continue

            except GameRoomExit:
                winners = self.game.get_winners()
                await self.sess.send_event(Event(
                    name = 'GameFinished',
                    data = {'winners': winners},
                    must_know = True,
                ))
                break

            try:
                logger.debug('It is {!r}\'s turn', client_name)
                with self.game_room.lock_events_for(client_name):
                    action = await self.sess.request_action()
                    logger.debug('{!r} requested action: {!r}', client_name, action)

                    move_result = self.game.take_turn(name=str(client_name), action=action)
                    crashed: bool = move_result.match(
                        OK = lambda: False,
                        CRASH = lambda: True,
                    ) # type: ignore

                    if crashed:
                        await self.on_crash()

                    await self.sess.respond_ok()

                new_field_state = self.game.field.get_state()
                await self.game_room.broadcast(
                    lambda context: context.session.send_new_field_state(new_field_state),
                    lambda name: True,
                )
            except IllegalAction as e:
                logger.debug('The action {!r} for {!r} is invalid: {!r}', action, client_name, e)
                await self.sess.respond_err(str(e))
            finally:
                await self.game_room.finish_turn(client_name)

    async def on_crash(self) -> None:
        client_name = self.client_info.name
        logger.debug('{!r} crashed', client_name)

        await self.sess.respond_ok()
        self.game_room.mark_snake_dead(client_name)
        await self.game_room.report_death(client_name)

    async def on_disconnect(self) -> None:
        client_name = self.client_info.name
        logger.debug('{!r} disconnected from the game', client_name)

        self.game_room.mark_client_disconnected(client_name)
        if client_name.is_player():
            await self.game_room.report_disconnect(client_name)
