from bot_arena_server.server import Server
from bot_arena_server.game_loop import run_game_loop

from bot_arena_proto.session import ServerSession
from loguru import logger


__all__ = [
    'main',
]


def main():
    server = Server(run_game_loop)
    server.listen('127.0.0.1', 23456)


if __name__ == '__main__':
    main()
