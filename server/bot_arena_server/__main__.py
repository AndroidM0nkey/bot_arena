from bot_arena_server.server import Server
from bot_arena_server.game_loop import run_game_loop

import sys
from argparse import ArgumentParser, Namespace

from loguru import logger


__all__ = [
    'main',
]


def parse_args() -> Namespace:
    ap = ArgumentParser(prog='bot-arena-server', description='Pythons game server')
    ap.add_argument('--listen-on', default='0.0.0.0', help='IP address or domain name to listen on')
    ap.add_argument('--port', '-p', type=int, default=23456, help='Port to listen on')
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    logger.remove()
    logger.add(sys.stderr, level='INFO')
    server = Server(run_game_loop)
    server.listen(args.listen_on, args.port)


if __name__ == '__main__':
    main()
