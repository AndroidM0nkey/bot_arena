from bot_arena_proto.data import Action, FieldState
from bot_arena_proto.event import Event
from bot_arena_proto.message import Message

from dataclasses import dataclass
from time import sleep
from typing import Protocol, Tuple

from adt import adt, Case


MAX_SANE_LENGTH = 2**20  # 1 MiB should be much more than enough


class Stream(Protocol):
    def read(self, how_many: int) -> bytes:
        ...

    def write(self, data: bytes) -> bytes:
        ...


class Session:
    def __init__(self, stream: Stream) -> None:
        self._stream = stream

    def send_message(self, message: Message) -> None:
        self._send_frame(message.to_bytes())

    def recv_message(self) -> Message:
        return Message.from_bytes(self._recv_frame())

    def _send_frame(self, data: bytes):
        assert len(data) <= MAX_SANE_LENGTH
        self._write_bytes(len(data).to_bytes(8, 'little', signed=False))
        self._write_bytes(data)

    def _recv_frame(self) -> bytes:
        length = int.from_bytes(self._read_bytes(8), 'little', signed=False)
        if length > MAX_SANE_LENGTH:
            raise ValueError(f'Length limit exceeded: cannot receive a {length}-byte frame')
        return self._read_bytes(length)

    def _write_bytes(self, data: bytes) -> None:
        self._stream.write(data)

    def _read_bytes(self, how_many: int) -> bytes:
        buf = bytearray()
        while len(buf) < how_many:
            bytes_still_to_read = how_many - len(buf)
            buf += self._stream.read(bytes_still_to_read)
        return bytes(buf)


class ClientSession(Session):
    def __init__(self, stream: Stream, client_info: 'ClientInfo') -> None:
        super().__init__(stream)
        self._info = client_info

    def initialize(self):
        self.send_message(Message.CLIENT_HELLO(self._info.name))
        self.recv_message().server_hello()

    def ready(self):
        self.send_message(Message.READY())

    def wait_until_game_started(self) -> 'GameInfo':
        def err(e):
            def inner(*args):
                raise e
            return inner

        def unexpected(s):
            return err(
                ValueError(
                    f'Unexpected event received from the server before the game has started: {s}'
                )
            )

        while True:
            event = self.wait_for_notification().event()
            result = event.match(
                snake_died = unexpected('SnakeDied'),
                game_finished = unexpected('GameFinished'),
                game_started = lambda width, height: (width, height),
            )
            width, height = result
            return GameInfo(field_width=width, field_height=height)

    def wait_for_notification(self) -> 'ClientNotification':
        def err(e):
            def inner(*args):
                raise e
            return inner

        def unexpected(s):
            return err(ValueError(f'Unexpected message received from the server: {s}'))

        while True:
            result = self.recv_message().match(
                client_hello = unexpected('ClientHello'),
                server_hello = unexpected('ServerHello'),
                your_turn = lambda: ClientNotification.REQUEST(),
                ready = unexpected('Ready'),
                new_field_state = lambda state: ClientNotification.FIELD_STATE(state),
                act = unexpected('Act'),
                event_happened = lambda ev: ClientNotification.EVENT(ev),
                ok = lambda: None,
                err = lambda text: ClientNotification.ERROR(text),
            )
            if result is not None:
                return result

    def respond(self, action: Action) -> None:
        self.send_message(Message.ACT(action))


class ServerSession(Session):
    def pre_initialize(self) -> 'ClientInfo':
        client_msg = self.recv_message()
        name = client_msg.client_hello()
        return ClientInfo(name=name)

    def initialize_ok(self) -> None:
        self.send_message(Message.SERVER_HELLO())

    def initialize_err(self, text: str) -> None:
        self.send_message(Message.ERR(text))

    def start_game(self, game_info: 'GameInfo') -> None:
        width = game_info.field_width
        height = game_info.field_height
        self.send_event(Event.GAME_STARTED(width, height))

    def wait_until_ready(self) -> None:
        client_msg = self.recv_message()
        client_msg.ready()

    def send_new_field_state(self, state: FieldState) -> None:
        self.send_message(Message.NEW_FIELD_STATE(state))

    def send_event(self, event: Event) -> None:
        self.send_message(Message.EVENT_HAPPENED(event))

    def request_action(self) -> Action:
        self.send_message(Message.YOUR_TURN())
        client_msg = self.recv_message()
        return client_msg.act()

    def respond_ok(self) -> None:
        self.send_message(Message.OK())

    def respond_err(self, text: str) -> None:
        self.send_message(Message.ERR(text))


@dataclass
class GameInfo:
    field_width: int
    field_height: int


@dataclass
class ClientInfo:
    name: str


@adt
class ClientNotification:
    REQUEST: Case
    FIELD_STATE: Case[FieldState]
    EVENT: Case[Event]
    ERROR: Case[str]
