from bot_arena_server.game import Game, IllegalAction
from bot_arena_server.game_room import GameRoom
from bot_arena_server.client_name import RichClientInfo

from typing import NoReturn

import curio # type: ignore
from bot_arena_proto.event import Event
from bot_arena_proto.session import ServerSession, GameInfo, ClientInfo
from loguru import logger # type: ignore


__all__ = [
    'run_game_loop',
]


async def wait_forever() -> NoReturn:
    while True:
        await curio.sleep(10000)


async def run_game_loop(
    sess: ServerSession,
    client_info: RichClientInfo,
    game: Game,
    game_room: GameRoom,
) -> None:
    game_room.set_session(client_info.name, sess)
    await sess.send_new_field_state(game.field.get_state())

    if not client_info.name.is_player():
        # TODO: wait for either the player's action or the end of the game.
        await wait_forever()
        return

    while True:
        await game_room.wait_for_turn(client_info.name)
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
