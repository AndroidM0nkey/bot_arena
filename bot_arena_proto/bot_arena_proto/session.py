from bot_arena_proto.data import Action, FieldState
from bot_arena_proto.event import Event
from bot_arena_proto.message import Message

from typing import Protocol

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
            self._stream.read(bytes_still_to_read)
        return bytes(buf)


class ClientSession(Session):
    def __init__(self, stream: Stream, name: str) -> None:
        super().__init__(stream)

    def initialize(self) -> Tuple[int, int]:
        self.send_message(Message.CLIENT_HELLO(name))
        response = self.recv_message()
        field_dimensions = response.server_hello()
        self.send_message(Message.READY())
        return field_dimensions

    def wait_for_notification(self) -> ClientNotification:
        def err(e):
            def inner(*args):
                raise e
            return inner

        def unexpected(s):
            return err(f'Unexpected message received from server: {s}')

        while True:
            result = self.recv_message().match(
                client_hello = unexpected('CLIENT_HELLO'),
                server_hello = unexpected('SERVER_HELLO'),
                your_turn = lambda: ClientNotification.REQUEST(),
                ready = unexpected('READY'),
                new_field_state = lambda state: ClientNotification.FIELD_STATE(state),
                act = unexpected('ACT'),
                event_happened = lambda ev: ClientNotification.EVENT(ev),
                ok = lambda: None,
                err = lambda text: ClientNotification.ERROR(text),
            )
            if result is not None:
                return result

    def respond(self, action: Action) -> None:
        self.send_message(Message.ACTION(action))


class ServerSession(Session):
    def initialize(self, field_size: Tuple[int, int]) -> str:
        client_msg = self.recv_message()
        name = client_msg.client_hello()
        self.send_message(Message.SERVER_HELLO(field_size))

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
        return client_msg.action()

    def respond_ok(self) -> None:
        self.send_message(Message.OK())

    def respond_err(self, text: str) -> None:
        self.send_message(Message.ERR(text))


@adt
class ClientNotification:
    REQUEST: Case
    FIELD_STATE: Case[FieldState]
    EVENT: Case[Event]
    ERROR: Case[str]
