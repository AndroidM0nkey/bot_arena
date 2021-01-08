import re

from bot_arena_proto.session import ServerSession, GameInfo
from loguru import logger


__all__ = [
    'run_game_loop',
]


def is_name_valid(name):
    return re.match(r'^[a-zA-Z0-9_-]+$', name) is not None


async def run_game_loop(sess: ServerSession) -> None:
    # TODO: this is just a stub. It does not contain any actual game logic.
    player_info = await sess.pre_initialize()
    if not is_name_valid(player_info.name):
        await sess.respond_err('Invalid or unacceptable player name')
        return

    logger.info('{} joined the party', player_info.name)
    await sess.initialize_ok()

    await sess.wait_until_ready()
    game_info = GameInfo(field_height=20, field_width=30)
    await sess.start_game(game_info)
    logger.info('Game with {} has started', player_info.name)

    while True:
        logger.info('It\'s {}\'s turn', player_info.name)
        action = await sess.request_action()
        logger.info('{} requested action: {}', player_info.name, action)
        await sess.respond_ok()
