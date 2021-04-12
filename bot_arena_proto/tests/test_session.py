import pytest

from bot_arena_proto.session import ClientSession, ServerSession, ClientInfo, GameInfo
from bot_arena_proto.event import Event
from bot_arena_proto.data import FieldState, Direction, Point, SnakeState, Object, Action

import sys
from queue import Queue, Empty
from types import coroutine


class FakeStream:
    def __init__(self):
        self._q12 = Queue(maxsize=-1)
        self._q21 = Queue(maxsize=-1)
        self._buf12 = bytearray()
        self._buf21 = bytearray()

    @coroutine
    def read1(self, size: int):
        while True:
            if len(self._buf21) > 0:
                data = self._buf21[:size]
                self._buf21 = self._buf21[size:]
                return bytes(data)
            try:
                self._buf21 += self._q21.get_nowait()
            except Empty:
                yield 'read'
                self._buf21 += self._q21.get_nowait()
            assert len(self._buf21) > 0

    @coroutine
    def read2(self, size: int):
        while True:
            if len(self._buf12) > 0:
                data = self._buf12[:size]
                self._buf12 = self._buf12[size:]
                return bytes(data)
            try:
                self._buf12 += self._q12.get_nowait()
            except Empty:
                yield 'read'
                self._buf12 += self._q12.get_nowait()
            assert len(self._buf12) > 0

    @coroutine
    def write1(self, data: bytes):
        self._q12.put(data)
        yield 'written'

    @coroutine
    def write2(self, data: bytes):
        self._q21.put(data)
        yield 'written'

    def pipe(self):
        return Endpoint(self, 1), Endpoint(self, 2)


class Endpoint:
    def __init__(self, fake_stream: FakeStream, n: int):
        self.fake_stream = fake_stream
        self.n = n

    async def read(self, size: int) -> bytes:
        b = await getattr(self.fake_stream, f'read{self.n}')(size)
        print(f'Read({self.n}) {size} -> {b}')
        return b

    async def write(self, data: bytes):
        print(f'Write({self.n}) {data}')
        return await getattr(self.fake_stream, f'write{self.n}')(data)


def run(a, b):
    last = None

    try:
        while True:
            last = a
            ar = a.send(None)
            print(f'{ar = }')
            if ar == 'read':
                last = b
                br = b.send(None)
                print(f'{br = }')
                assert br == 'written'
            else:
                assert ar == 'written'
                print('swap!')
                a, b = b, a
    except StopIteration:
        pass

    try:
        while True:
            if last is a:
                b.send(None)
            else:
                a.send(None)
    except StopIteration:
        pass


def print_now(*a, **k):
    print(*a, **k)
    sys.stdout.flush()


async def client_session(endpoint):
    print_now('Client: starting')
    sess = ClientSession(endpoint, client_info=ClientInfo(name='Python39'))
    print_now('Client: created session')
    await sess.initialize()
    print_now('Client: sess.initialize() called')
    await sess.ready()
    print_now('Client: sess.ready() called')
    game_info = await sess.wait_until_game_started()
    width = game_info.field_width
    height = game_info.field_height
    print_now('Client: game started')
    assert (width, height) == (18, 22)

    (await sess.wait_for_notification()).request()
    print_now('Client: got action request')

    with pytest.raises(Exception, match = 'Illegal move'):
        await sess.respond(Action.MOVE(Direction.LEFT()))
        print_now('Client: move left')

    (await sess.wait_for_notification()).request()
    print_now('Client: my turn once again')
    await sess.respond(Action.MOVE(Direction.UP()))
    print_now('Client: now move up')

    fs = (await sess.wait_for_notification()).field_state()
    print_now('Client: received field state update')
    assert fs == FieldState(
        snakes = {
            'Bob': SnakeState(head=Point(3, 4), tail=[Direction.DOWN()]),
        },
        objects = [
            (Point(1, 0), Object.FOOD()),
        ]
    )

    (await sess.wait_for_notification()).event().game_finished()
    print_now('Client: game finished')


async def server_session(endpoint):
    print_now('Server: starting')
    sess = ServerSession(endpoint)
    print_now('Server: created session')
    client_info = await sess.pre_initialize()
    name = client_info.name
    print_now('Server: sess.pre_initialize() called')
    assert name == 'Python39'
    print_now('Server: name ok')
    await sess.initialize_ok()
    print_now('Server: initialized')

    await sess.wait_until_ready()
    print_now('Server: client is ready')
    await sess.start_game(game_info=GameInfo(field_width=18, field_height=22))
    print_now('Server: game started')

    action = await sess.request_action()
    print_now('Server: player responded with an action')
    assert action == Action.MOVE(Direction.LEFT())
    await sess.respond_err('Illegal move')
    print_now('Server: informed the player about an illegal move')
    another_action = await sess.request_action()
    print_now('Server: player responded with another action')
    assert another_action == Action.MOVE(Direction.UP())
    await sess.respond_ok()
    print_now('Server: accepted player\'s action')
    await sess.send_new_field_state(
        FieldState(
            snakes = {
                'Bob': SnakeState(head=Point(3, 4), tail=[Direction.DOWN()]),
            },
            objects = [
                (Point(1, 0), Object.FOOD()),
            ]
        )
    )
    print_now('Server: sent new field state')
    await sess.send_event(Event.GAME_FINISHED())
    print_now('Server: game finished')


def test_session():
    fake_stream = FakeStream()
    a, b = fake_stream.pipe()
    run(client_session(a), server_session(b))
