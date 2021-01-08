from bot_arena_server.server import Server

from bot_arena_proto.session import ServerSession


__all__ = [
    'main',
]


async def handle_client(sess: ServerSession):
    # TODO
    print('(session)')


def main():
    server = Server(handle_client)
    server.listen('127.0.0.1', 23456)


if __name__ == '__main__':
    main()
