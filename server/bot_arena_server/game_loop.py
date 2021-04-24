from bot_arena_server.game import Game, IllegalAction
from bot_arena_server.game_room import GameRoom, GameRoomExit
from bot_arena_server.client_name import RichClientInfo

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
    game_room.set_session(client_info.name, sess)
    await sess.send_event(Event(name='GameStarted', data=game.info().to_primitive(), must_know=True))
    await sess.send_new_field_state(game.field.get_state())

    try:
        if not client_info.name.is_player():
            await game_room.wait_until_game_ends()
            await sess.send_event(Event(name='GameFinished', data=None, must_know=True))
            return

        while True:
            try:
                await game_room.wait_for_turn(client_info.name)
            except GameRoomExit:
                logger.debug('{!r} leaves the room because of their death', client_info.name)
                await sess.send_event(Event(name='GameFinished', data=None, must_know=True))
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
                    logger.info('{!r} died', client_info.name)
                    await on_crash(sess, client_info, game_room)
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
                await sess.respond_err(str(e))
    except Exception:
        logger.info('{!r} disconnected', client_info.name)
        await on_crash(sess, client_info, game_room, report_to_offender=False)
        raise


async def on_crash(
    sess: ServerSession,
    client_info: RichClientInfo,
    game_room: GameRoom,
    report_to_offender: bool = True,
) -> None:
    if report_to_offender:
        logger.debug('1a, {}', client_info.name)
        await sess.respond_ok()
        logger.debug('2a, {}', client_info.name)
        await game_room.report_death(client_info.name)
        logger.debug('3a, {}', client_info.name)
        game_room.mark_snake_dead(client_info.name)
        logger.debug('4a, {}', client_info.name)
    else:
        logger.debug('1, {}', client_info.name)
        game_room.mark_snake_dead(client_info.name)
        logger.debug('2, {}', client_info.name)
        await game_room.report_death(client_info.name)
        logger.debug('3, {}', client_info.name)

    await game_room.finish_turn(client_info.name)
    logger.debug('4, {}', client_info.name)
