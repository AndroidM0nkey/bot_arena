from bot_arena_server.game import Game, IllegalAction

from bot_arena_proto.session import ServerSession, GameInfo, ClientInfo
from loguru import logger


__all__ = [
    'run_game_loop',
]


async def run_game_loop(sess: ServerSession, client_info: ClientInfo, game: Game) -> None:
    while True:
        logger.info('It\'s {}\'s turn', client_info.name)
        action = await sess.request_action()
        logger.info('{} requested action: {}', client_info.name, action)

        try:
            game.take_turn(name=client_info.name, action=action)
            await sess.respond_ok()
        except IllegalAction as e:
            logger.info('The action {} for {} is invalid: {}', action, client_info.name, e)
            await sess.respond_err(text=str(e))
