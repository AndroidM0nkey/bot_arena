from bot_arena_proto.data import Action, FieldState
from bot_arena_proto.event import Event
from bot_arena_proto.message import Message

from dataclasses import dataclass
from time import sleep
from typing import Protocol, Tuple

from adt import adt, Case


__all__ = [
    'ClientInfo',
    'ClientNotification',
    'ClientSession',
    'GameInfo',
    'MAX_SANE_LENGTH',
    'ServerSession',
    'Session',
    'Stream',
]


MAX_SANE_LENGTH = 2**20  # 1 MiB should be much more than enough


class Stream(Protocol):
    """A protocol describing a byte stream which can be read from and written to."""

    def read(self, how_many: int) -> bytes:
        """Read and return at most `how_many` bytes from the stream.

        This method is expected to block until some bytes are available
        in the cahnnel.
        """

        ...

    def write(self, data: bytes) -> bytes:
        """Write the specified byte string to the stream."""

        ...


class Session:
    """Base class for client and server sessions."""

    def __init__(self, stream: Stream) -> None:
        """Initialize self.

        Parameters:
            stream: The underlying byte stream (see Stream). Usually,
                    a TCP network stream, but, in theory, may have
                    a different nature.
        """

        self._stream = stream

    def send_message(self, message: Message) -> None:
        """Send the specified message to the peer on the other end of the stream."""

        self._send_frame(message.to_bytes())

    def recv_message(self) -> Message:
        """Receive a message from the peer on the other end of the
        stream.

        This method blocks until a message is completely read from
        the underlying stream.
        """

        return Message.from_bytes(self._recv_frame())

    def _send_frame(self, data: bytes):
        """[Internal] Send a string of bytes together with its length."""

        assert len(data) <= MAX_SANE_LENGTH
        self._write_bytes(len(data).to_bytes(8, 'little', signed=False))
        self._write_bytes(data)

    def _recv_frame(self) -> bytes:
        """[Internal] Receive a string of bytes together with its length."""

        length = int.from_bytes(self._read_bytes(8), 'little', signed=False)
        if length > MAX_SANE_LENGTH:
            # Prevents a malicious user from crashing the server by sending it
            # a multi-gigabyte message, forcing it to run out of RAM.
            raise ValueError(f'Length limit exceeded: cannot receive a {length}-byte frame')
        return self._read_bytes(length)

    def _write_bytes(self, data: bytes) -> None:
        """[Internal] Write a byte string to the underlying stream."""

        self._stream.write(data)

    def _read_bytes(self, how_many: int) -> bytes:
        """[Internal] Read at most `how_many` bytes from the underlying stream."""

        buf = bytearray()
        while len(buf) < how_many:
            bytes_still_to_read = how_many - len(buf)
            buf += self._stream.read(bytes_still_to_read)
        return bytes(buf)


class ClientSession(Session):
    """The client side of a session."""

    def __init__(self, stream: Stream, client_info: 'ClientInfo') -> None:
        """Initialize self.

        Parameters:
            stream:         Underlying stream (see Session).
            client_info:    An object containing the information about
                            the client (see ClientInfo).
        """

        super().__init__(stream)
        self._info = client_info

    def initialize(self):
        """Send a CLIENT_HELLO and receive a SERVER_HELLO.

        WARNING: Calling .initialize() alone is not enough to
        start the game! You also have to call .ready() to
        signal to the server that you are ready to start.
        This is so because, potentially, some actions may be allowed
        after the client has connected but before the game actually
        starts. These may include such things as choosing a game room,
        listing the players or changing the name.

        FIXME: Raises an obscure exception when the server does not
        respond with a SERVER_HELLO (e.g. when it responds with ERR
        instead). This is planned to be caught and replaced with
        a more informative exception.
        """

        self.send_message(Message.CLIENT_HELLO(self._info.name))
        self.recv_message().server_hello()

    def ready(self):
        """Signal to the server that you are ready to begin the game by
        sending it a READY message.
        """

        self.send_message(Message.READY())

    def wait_until_game_started(self) -> 'GameInfo':
        """Wait until the game is actually started.

        This includes waiting until other players signal their readiness
        to the server.

        Returns a GameInfo object, which contains information about
        the current game. See GameInfo for details.
        """

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
        """Wait until the server notifies you about something.

        The possible types of notifications are described in the
        documentation for the ClientNotification class.
        """

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
        """Respond to a YOUR_TURN message with an Action."""

        self.send_message(Message.ACT(action))


class ServerSession(Session):
    """The server side of the session."""

    def pre_initialize(self) -> 'ClientInfo':
        """Receive a CLIENT_HELLO message and return the attached ClientInfo object."""

        client_msg = self.recv_message()
        name = client_msg.client_hello()
        return ClientInfo(name=name)

    def initialize_ok(self) -> None:
        """Respond with a SERVER_HELLO (indicating success) to a CLIENT_HELLO."""

        self.send_message(Message.SERVER_HELLO())

    def initialize_err(self, text: str) -> None:
        """Respond with an ERR (with the specified error message) to a CLIENT_HELLO."""

        self.send_message(Message.ERR(text))

    def start_game(self, game_info: 'GameInfo') -> None:
        """Start a game.

        The provided GameInfo object is sent to the client as the
        parameter of a GAME_STARTED message.
        """

        width = game_info.field_width
        height = game_info.field_height
        self.send_event(Event.GAME_STARTED(width, height))

    def wait_until_ready(self) -> None:
        """Wait unitl a client sends READY."""

        client_msg = self.recv_message()
        client_msg.ready()

    def send_new_field_state(self, state: FieldState) -> None:
        """Send a new field state to the client."""

        self.send_message(Message.NEW_FIELD_STATE(state))

    def send_event(self, event: Event) -> None:
        """Inform the client about an event."""

        self.send_message(Message.EVENT_HAPPENED(event))

    def request_action(self) -> Action:
        """Inform the client that it is their turn now and request their action."""

        self.send_message(Message.YOUR_TURN())
        client_msg = self.recv_message()
        return client_msg.act()

    def respond_ok(self) -> None:
        """Send OK."""

        self.send_message(Message.OK())

    def respond_err(self, text: str) -> None:
        """Send ERR."""

        self.send_message(Message.ERR(text))


@dataclass
class GameInfo:
    """Stores the information about a game.

    Currently, contains only `field_width` and `field_height`,
    which describe the dimensions of the game field.
    """

    field_width: int
    field_height: int


@dataclass
class ClientInfo:
    """Stores the information about a client.

    Fields:
        name:   The name of the player.
    """

    name: str


@adt
class ClientNotification:
    """A notification sent by the server to the client.

    Currently supported values:

    - REQUEST:      The server informed you that it is your turn now and
                    requests an action from you.

    - FIELD_STATE:  The server sends you an updated field state.

    - EVENT:        The server informs you about an event (see
                    bot_arena_proto.event.Event).

    - ERROR:        The server informs you about an error (corresponds
                    to an ERR message).
    """

    REQUEST: Case
    FIELD_STATE: Case[FieldState]
    EVENT: Case[Event]
    ERROR: Case[str]
