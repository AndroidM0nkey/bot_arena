from bot_arena_server.game import Game, IllegalAction
from bot_arena_server.game_room import GameRoom

from bot_arena_proto.event import Event
from bot_arena_proto.session import ServerSession, GameInfo, ClientInfo
from loguru import logger


__all__ = [
    'run_game_loop',
]


async def run_game_loop(
    sess: ServerSession,
    client_info: ClientInfo,
    game: Game,
    game_room: GameRoom,
) -> None:
    while True:
        await game_room.wait_for_turn(client_info.name)

        logger.info('It is {}\'s turn', client_info.name)
        action = await sess.request_action()
        logger.info('{} requested action: {}', client_info.name, action)

        try:
            move_result = game.take_turn(name=client_info.name, action=action)
            crashed = move_result.match(
                OK = lambda: False,
                CRASH = lambda: True,
            )

            if crashed:
                await on_crash(sess, client_info),
                break
            else:
                await sess.respond_ok()

            logger.debug(game.field.get_state())
        except IllegalAction as e:
            logger.info('The action {} for {} is invalid: {}', action, client_info.name, e)
            await sess.respond_err(text=str(e))


async def on_crash(sess: ServerSession, client_info: ClientInfo) -> None:
    logger.info('{} died', client_info.name)
    await sess.respond_ok()

    # TODO: broadcast this message
    await sess.send_event(Event.SNAKE_DIED(client_info.name))
