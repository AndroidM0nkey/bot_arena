from bot_arena_proto.session import ClientSession, ServerSession, ClientInfo, GameInfo
from bot_arena_proto.event import Event
from bot_arena_proto.data import FieldState, Direction, Point, SnakeState, Object, Action

import sys
from threading import Thread, Lock
from queue import Queue


class FakeStream:
    def __init__(self):
        self._q12 = Queue(maxsize=-1)
        self._q21 = Queue(maxsize=-1)
        self._buf12 = bytearray()
        self._buf21 = bytearray()

    def read1(self, size: int) -> bytes:
        while True:
            if len(self._buf21) > 0:
                data = self._buf21[:size]
                self._buf21 = self._buf21[size:]
                return data
            self._buf21 += self._q21.get()
            assert len(self._buf21) > 0

    def read2(self, size: int) -> bytes:
        while True:
            if len(self._buf12) > 0:
                data = self._buf12[:size]
                self._buf12 = self._buf12[size:]
                return data
            self._buf12 += self._q12.get()
            assert len(self._buf12) > 0

    def write1(self, data: bytes):
        self._q12.put(data)

    def write2(self, data: bytes):
        self._q21.put(data)

    def pipe(self):
        return Endpoint(self, 1), Endpoint(self, 2)


class Endpoint:
    def __init__(self, fake_stream: FakeStream, n: int):
        self.fake_stream = fake_stream
        self.n = n

    def read(self, size: int) -> bytes:
        return getattr(self.fake_stream, f'read{self.n}')(size)

    def write(self, data: bytes):
        return getattr(self.fake_stream, f'write{self.n}')(data)


CLIENT_THREAD_RESULT = None
SERVER_THREAD_RESULT = None


def print_now(*a, **k):
    print(*a, **k)
    sys.stdout.flush()


def client_session(endpoint):
    global CLIENT_THREAD_RESULT
    try:
        print_now('Client: starting')
        sess = ClientSession(endpoint, client_info=ClientInfo(name='Python39'))
        print_now('Client: created session')
        sess.initialize()
        print_now('Client: sess.initialize() called')
        sess.ready()
        print_now('Client: sess.ready() called')
        game_info = sess.wait_until_game_started()
        width = game_info.field_width
        height = game_info.field_height
        print_now('Client: game started')
        assert (width, height) == (18, 22)

        sess.wait_for_notification().request()
        print_now('Client: got action request')
        sess.respond(Action.MOVE(Direction.LEFT()))
        print_now('Client: move left')
        assert sess.wait_for_notification().error() == 'Illegal move'
        print_now('Client: ok, this was wrong')

        sess.wait_for_notification().request()
        print_now('Client: my turn once again')
        sess.respond(Action.MOVE(Direction.UP()))
        print_now('Client: now move up')

        fs = sess.wait_for_notification().field_state()
        print_now('Client: received field state update')
        assert fs == FieldState(
            snakes = {
                'Bob': SnakeState(head=Point(3, 4), tail=[Direction.DOWN()]),
            },
            objects = [
                (Point(1, 0), Object.FOOD()),
            ]
        )

        sess.wait_for_notification().event().game_finished()
        print_now('Client: game finished')
        CLIENT_THREAD_RESULT = 'ok'
    except BaseException as e:
        CLIENT_THREAD_RESULT = e


def server_session(endpoint):
    global SERVER_THREAD_RESULT
    try:
        print_now('Server: starting')
        sess = ServerSession(endpoint)
        print_now('Server: created session')
        client_info = sess.pre_initialize()
        name = client_info.name
        print_now('Server: sess.pre_initialize() called')
        assert name == 'Python39'
        print_now('Server: name ok')
        sess.initialize_ok()
        print_now('Server: initialized')

        sess.wait_until_ready()
        print_now('Server: client is ready')
        sess.start_game(game_info=GameInfo(field_width=18, field_height=22))
        print_now('Server: game started')

        action = sess.request_action()
        print_now('Server: player responded with an action')
        assert action == Action.MOVE(Direction.LEFT())
        sess.respond_err('Illegal move')
        print_now('Server: informed the player about an illegal move')
        another_action = sess.request_action()
        print_now('Server: player responded with another action')
        assert another_action == Action.MOVE(Direction.UP())
        sess.respond_ok()
        print_now('Server: accepted player\'s action')
        sess.send_new_field_state(
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
        sess.send_event(Event.GAME_FINISHED())
        print_now('Server: game finished')
        SERVER_THREAD_RESULT = 'ok'
    except BaseException as e:
        SERVER_THREAD_RESULT = e


def test_session():
    fake_stream = FakeStream()
    a, b = fake_stream.pipe()
    client_thread = Thread(target=client_session, args=[a], daemon=True)
    server_thread = Thread(target=server_session, args=[b], daemon=True)
    client_thread.start()
    server_thread.start()
    client_thread.join(timeout=3)
    server_thread.join(timeout=3)
    print(f'Client thread result: {CLIENT_THREAD_RESULT}')
    print(f'Server thread result: {SERVER_THREAD_RESULT}')
    assert not client_thread.is_alive()
    assert not server_thread.is_alive()
    assert CLIENT_THREAD_RESULT == 'ok'
    assert SERVER_THREAD_RESULT == 'ok'
