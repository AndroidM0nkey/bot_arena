from bot_arena_server.game import Game, IllegalAction
from bot_arena_server.game_room import GameRoom, GameRoomExit
from bot_arena_server.client_name import RichClientInfo

from typing import NoReturn

import curio # type: ignore
from bot_arena_proto.event import Event
from bot_arena_proto.message import Message
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
    game_room.set_session(client_info.name, sess)
    await sess.send_new_field_state(game.field.get_state())

    if not client_info.name.is_player():
        await game_room.wait_until_game_ends()
        return

    while True:
        try:
            async with curio.TaskGroup(wait=any) as tg:
                await tg.spawn(sess.recv_message())                         # Returns Message
                await tg.spawn(game_room.wait_for_turn(client_info.name))   # Returns None
            await tg.cancel_remaining()

            if tg.result is not None:
                logger.debug('Received an out of order message from {!r}', client_info.name)
                assert isinstance(tg.result, Message)
                await sess.respond_err('It is not your turn')
                continue
        except GameRoomExit:
            break

        logger.info('It is {}\'s turn', client_info.name)
        action = await sess.request_action()
        logger.info('{} requested action: {}', client_info.name, action)

        try:
            move_result = game.take_turn(name=str(client_info.name), action=action)
            crashed: bool = move_result.match(
                OK = lambda: False,
                CRASH = lambda: True,
            ) # type: ignore

            if crashed:
                await on_crash(sess, client_info, game_room)
                await game_room.finish_turn(client_info.name)
                break
            else:
                await sess.respond_ok()

            new_field_state = game.field.get_state()
            await game_room.broadcast(
                lambda sess: sess.send_new_field_state(new_field_state),
                lambda name: True,
            )
        except IllegalAction as e:
            logger.info('The action {} for {} is invalid: {}', action, client_info.name, e)
            await sess.respond_err(text=str(e))


async def on_crash(sess: ServerSession, rich_client_info: RichClientInfo, game_room: GameRoom) -> None:
    logger.info('{!r} died', rich_client_info.name)
    await sess.respond_ok()
    await game_room.report_death(rich_client_info.name)
