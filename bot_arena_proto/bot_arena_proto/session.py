from bot_arena_proto.data import Action, FieldState, RoomInfo
from bot_arena_proto.event import Event
from bot_arena_proto.message import Message
from bot_arena_proto.serialization import ensure_type

from dataclasses import dataclass
from time import sleep
from typing import Protocol, Tuple, Any, List, Dict

from adt import adt, Case


__all__ = [
    'ClientInfo',
    'ClientNotification',
    'ClientSession',
    'GameInfo',
    'MAX_SANE_LENGTH',
    'ServerSession',
    'Session',
    'AsyncStream',
]


MAX_SANE_LENGTH = 2**20  # 1 MiB should be much more than enough


class AsyncStream(Protocol):
    """A protocol describing a byte stream which can be read from and written to."""

    async def read(self, how_many: int) -> bytes:
        """Read and return at most `how_many` bytes from the stream."""
        ...

    async def write(self, data: bytes) -> bytes:
        """Write the specified byte string to the stream."""
        ...


class Session:
    """Base class for client and server sessions."""

    def __init__(self, stream: AsyncStream) -> None:
        """Initialize self.

        Parameters:
            stream: The underlying byte stream (see AsyncStream). Usually,
                    an async TCP network stream (such as TCP streams provided
                    by libraries like asyncio or curio, but, in theory, may have
                    a different nature.
        """

        self._stream = stream

    async def send_message(self, message: Message) -> None:
        """Send the specified message to the peer on the other end of the stream."""

        await self._send_frame(message.to_bytes())

    async def recv_message(self) -> Message:
        """Receive a message from the peer on the other end of the
        stream.
        """

        return Message.from_bytes(await self._recv_frame())

    async def _send_frame(self, data: bytes):
        """[Internal] Send a string of bytes together with its length."""

        assert len(data) <= MAX_SANE_LENGTH
        await self._write_bytes(len(data).to_bytes(8, 'little', signed=False))
        await self._write_bytes(data)

    async def _recv_frame(self) -> bytes:
        """[Internal] Receive a string of bytes together with its length."""

        length = int.from_bytes(await self._read_bytes(8), 'little', signed=False)
        if length > MAX_SANE_LENGTH:
            # Prevents a malicious user from crashing the server by sending it
            # a multi-gigabyte message, forcing it to run out of RAM.
            raise ValueError(f'Length limit exceeded: cannot receive a {length}-byte frame')
        return await self._read_bytes(length)

    async def _write_bytes(self, data: bytes) -> None:
        """[Internal] Write a byte string to the underlying stream."""

        await self._stream.write(data)

    async def _read_bytes(self, how_many: int) -> bytes:
        """[Internal] Read exactly `how_many` bytes from the underlying stream."""

        buf = bytearray()
        while len(buf) < how_many:
            bytes_still_to_read = how_many - len(buf)
            new_data = await self._stream.read(bytes_still_to_read)
            if len(new_data) == 0:
                raise EOFError('No more data available to read')
            buf += new_data
        return bytes(buf)


class ClientSession(Session):
    """The client side of a session."""

    def __init__(self, stream: AsyncStream, client_info: 'ClientInfo') -> None:
        """Initialize self.

        Parameters:
            stream:         Underlying stream (see Session).
            client_info:    An object containing the information about
                            the client (see ClientInfo).
        """

        super().__init__(stream)
        self._info = client_info

    async def initialize(self):
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

        await self.send_message(Message.CLIENT_HELLO(self._info.name))
        (await self.recv_message()).server_hello()

    async def ready(self):
        """Signal to the server that you are ready to begin the game by
        sending it a READY message.
        """

        await self.send_message(Message.READY())

    async def wait_until_game_started(self) -> 'GameInfo':
        """Wait until the game is actually started.

        This includes waiting until other players signal their readiness
        to the server.

        Returns a GameInfo object, which contains information about
        the current game. See GameInfo for details.
        """


        while True:
            event = (await self.wait_for_notification()).event()

            if event.name != 'GameStarted':
                raise ValueError(
                    f'Unexpected event received from the server before the game has started: {event}'
                )
            data = ensure_type(event.data, dict)
            width = ensure_type(data['field_width'], int)
            height = ensure_type(data['field_height'], int)
            return GameInfo(field_width=width, field_height=height)

    async def wait_for_notification(self) -> 'ClientNotification':
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
            result = (await self.recv_message()).match(
                client_hello = unexpected('ClientHello'),
                server_hello = unexpected('ServerHello'),
                your_turn = lambda: ClientNotification.REQUEST(),
                ready = unexpected('Ready'),
                new_field_state = lambda state: ClientNotification.FIELD_STATE(state),
                act = unexpected('Act'),
                event_happened = lambda ev: ClientNotification.EVENT(ev),
                ok = lambda: None,
                err = lambda text: ClientNotification.ERROR(text),
                list_rooms = unexpected('ListRooms'),
                enter_room = unexpected('EnterRoom'),
                enter_any_room = unexpected('EnterAnyRoom'),
                leave_room = unexpected('LeaveRoom'),
                new_room = unexpected('NewRoom'),
                get_room_properties = unexpected('GetRoomProperties'),
                set_room_properties = unexpected('SetRoomProperties'),
                room_list_available = unexpected('RoomListAvailable'),
                room_properties_available = unexpected('RoomPropertiesAvailable'),
            )
            if result is not None:
                return result

    async def respond(self, action: Action) -> None:
        """Respond to a YOUR_TURN message with an Action."""

        await self.send_message(Message.ACT(action))
        await self.expect_ok()

    async def list_rooms(self) -> List[RoomInfo]:
        """List the game rooms on the server."""

        await self.send_message(Message.LIST_ROOMS())
        return (await self.recv_message()).room_list_available()

    async def enter_room(self, room_name: str) -> None:
        """Enter a room with a specified name."""

        await self.send_message(Message.ENTER_ROOM(room_name))
        await self.expect_ok()

    async def enter_any_room(self) -> None:
        """Enter any room at the server's discretion."""

        await self.send_message(Message.ENTER_ANY_ROOM())
        await self.expect_ok()

    async def new_room(self) -> None:
        """Create a new room and become its only admin."""

        await self.send_message(Message.NEW_ROOM())
        await self.expect_ok()

    async def get_room_properties(self) -> Dict[str, Any]:
        """Request the properties of your current room."""

        await self.send_message(Message.GET_ROOM_PROPERTIES())
        return (await self.recv_message()).room_properties_available()

    async def set_room_properties(self, properties: Dict[str, Any]) -> None:
        """Change the values of some of the room's properties."""

        await self.send_message(Message.SET_ROOM_PROPERTIES(properties))
        await self.expect_ok()

    async def expect_ok(self) -> None:
        """Ensure that the server responds with an Ok."""

        message = await self.recv_message()
        try:
            message.ok()
            return
        except AttributeError:
            pass

        try:
            error_message = message.err()
            raise Exception(error_message)
        except AttributeError:
            pass

        raise Exception(f'Unexpected response from the server: {message}')


class ServerSession(Session):
    """The server side of the session."""

    async def pre_initialize(self) -> 'ClientInfo':
        """Receive a CLIENT_HELLO message and return the attached ClientInfo object."""

        client_msg = await self.recv_message()
        name = client_msg.client_hello()
        return ClientInfo(name=name)

    async def initialize_ok(self) -> None:
        """Respond with a SERVER_HELLO (indicating success) to a CLIENT_HELLO."""

        await self.send_message(Message.SERVER_HELLO())

    async def initialize_err(self, text: str) -> None:
        """Respond with an ERR (with the specified error message) to a CLIENT_HELLO."""

        await self.send_message(Message.ERR(text))

    async def wait_for_hub_action(self) -> Message:
        """Wait until a player in the hub asks for an appropriate action.

        The player must be in the hub, not in a game or a game room.
        """

        ok = lambda *args: True
        fail = lambda *args: False

        while True:
            message = await self.recv_message()
            success = message.match(
                act                         = fail,
                client_hello                = fail,
                enter_any_room              = ok,
                enter_room                  = ok,
                err                         = fail,
                event_happened              = fail,
                get_room_properties         = fail,
                leave_room                  = fail,
                list_rooms                  = ok,
                new_field_state             = fail,
                new_room                    = ok,
                ok                          = fail,
                ready                       = fail,
                room_list_available         = fail,
                room_properties_available   = fail,
                server_hello                = fail,
                set_room_properties         = fail,
                your_turn                   = fail,
            )

            if success:
                return message
            else:
                self.respond_err("This message is invalid in the hub")

    async def wait_for_room_action(self) -> Message:
        """Wait until a player in a game room asks for an appropriate action.

        The player must be in the game room, but not in a game.
        """

        ok = lambda *args: True
        fail = lambda *args: False

        while True:
            message = await self.recv_message()
            success = message.match(
                act                         = fail,
                client_hello                = fail,
                enter_any_room              = fail,
                enter_room                  = fail,
                err                         = fail,
                event_happened              = fail,
                get_room_properties         = ok,
                leave_room                  = ok,
                list_rooms                  = fail,
                new_field_state             = fail,
                new_room                    = fail,
                ok                          = fail,
                ready                       = ok,
                room_list_available         = fail,
                room_properties_available   = fail,
                server_hello                = fail,
                set_room_properties         = ok,
                your_turn                   = fail,
            )

            if success:
                return message
            else:
                self.respond_err("This message is invalid in a game room")

    async def respond_with_room_list(self, rooms: List[RoomInfo]) -> None:
        """Send the list of RoomInfo objects describing the rooms currently available."""
        await self.send_message(Message.ROOM_LIST_AVAILABLE(rooms))

    async def respond_with_room_properties(self, properties: Dict[str, Any]) -> None:
        """Send the properties of the current game room."""
        await self.send_message(Message.ROOM_PROPERTIES_AVAILABLE(properties))

    async def start_game(self, game_info: 'GameInfo') -> None:
        """Start a game.

        The provided GameInfo object is sent to the client as the
        parameter of a GAME_STARTED message.
        """

        width = game_info.field_width
        height = game_info.field_height
        await self.send_event(
            Event(
                name = 'GameStarted',
                data = {'field_width': width, 'field_height': height},
                must_know = True,
            )
        )

    async def wait_until_ready(self) -> None:
        """Wait unitl a client sends READY."""

        client_msg = await self.recv_message()
        client_msg.ready()

    async def send_new_field_state(self, state: FieldState) -> None:
        """Send a new field state to the client."""

        await self.send_message(Message.NEW_FIELD_STATE(state))

    async def send_event(self, event: Event) -> None:
        """Inform the client about an event."""

        await self.send_message(Message.EVENT_HAPPENED(event))

    async def request_action(self) -> Action:
        """Inform the client that it is their turn now and request their action."""

        await self.send_message(Message.YOUR_TURN())
        client_msg = await self.recv_message()
        return client_msg.act()

    async def respond_ok(self) -> None:
        """Send OK."""

        await self.send_message(Message.OK())

    async def respond_err(self, text: str) -> None:
        """Send ERR."""

        await self.send_message(Message.ERR(text))


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
