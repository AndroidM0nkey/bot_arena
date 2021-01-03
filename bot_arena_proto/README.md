# BotArena protocol library

Provides a high-level and a low-level interface to the communication between a client and a server.
The low-level interface provides the facilities to send and receive messages. The high-level interface
builds upon this message exchange and provides an easier to use and perhaps more intuitive
set of functionality.

## API reference
This library attempts to provide the docstrings for every non-internal class, function and method.
These can be either vieved in the source code, or accessed by the Python's `help(...)`
function. For example, if you want to see the documentation for `message.Message`
you can either look into the `bot_arena_proto/message.py` file and find the `Message`
class there, or start the Python interpreter and type the following:

```python
from bot_arena_proto.message import Message
help(Message)
```

There are plans to generate the HTML and/or PDF versions of documentation using
tools like [Sphinx](https://sphinx-doc.org), but this is currently not a top priority
task.

## High-level API: Session
**Note**: unless explicitly stated otherwise, everything mentioned
resides in the `session` module.

The high-level interface provided by this library is session-oriented.
Whether this library is used on the client or the server side, the user
is expected to create a corresponding `Session` object (namely `ClientSession`
or `ServerSession`) to begin the communication.

### Client session
To construct a `ClientSession` object, you need to provide a stream from which
bytes can be read and to which they can be written and the information about
the client in the form of a `ClientInfo` object. The stream can be a TCP stream,
a named or unnamed pipe or even something that just emulates real `read` and `write`
operations. The necessary methods of a stream, `.read()` and `.write()`, are described
in the `Stream` protocol. The information about the client currently contains
only the name of the player (and the snake it controls).

After a `ClientSession` object has been created, it is necessary to call
`.initialize()` on it to complete the handshake between the client
and the server. Under the hood, it sends a `CLIENT_HELLO` and receives
a `SERVER_HELLO` message.

After that, the client has to call `.ready()` to signal to the server that
it is ready to enter a game. This is not done automatically by `.initialize()`
because potentially a client may want to perform some actions (e.g. list the players
or change the name) before the game starts, but after the handshake has been completed.
At the moment, there are no such supported actions, but they may be introduced later.

`.ready()` is non-blocking: it does not wait until the game is actually started.
To wait until this happens, the client should call the `.wait_until_game_started()`
method. It returns the `GameInfo` object sent to you by the server, where
there is information about the size of the game field.

When the game starts, the server is supposed to notify the client of any events and changes.
The method `.wait_for_notification()` blocks until a message from the server is received
and returns a `ClientNotification` object. It is an algebraic data type that represents
serveral possible types of notifications:

- `REQUEST`: The server asks you to take your turn.
- `FIELD_STATE`: A new state of the game field is available.
- `EVENT`: Some event has happened. See `event.Event` for details.
- `ERROR`: Indicates an error in your previous request or response.

When the server asks you to take turn, you are supposed to reply with an action (see `data.Action`).
This is what the `.respond()` method is for. You have to construct a `data.Action` object
and then call `.respond()` with this object being a parameter.

#### Example

This is an example on how to use the `ClientSession` class to communicate with a server
from the client side.

```python
from bot_arena_proto.data import *
from bot_arena_proto.event import Event
from bot_arena_proto.session import ClientSession, ClientInfo

# Just an example network client (needs nclib package)
from nclib import Netcat

# Session, shared between functions.
# A properly designed program should probably avoid
# using global variables, but this is just a tiny example.
sess = None

def main():
    global sess

    # Connect to the server, assuming it is listening on 127.0.0.1:1234.
    stream = Netcat(connect=('127.0.0.1', 1234))

    # [[[ Interesting things start here ]]]

    # Create a ClientSession
    client_info = ClientInfo(name='Player 1')
    sess = ClientSession(stream=stream, client_info=client_info)

    # Perform the handshake
    sess.initialize()

    ...  # Do what you want before being ready to enter a game

    # Start the game
    sess.ready()
    game_info = sess.wait_until_game_started()

    # Important data
    field_width = game_info.field_width
    field_height = game_info.field_height

    # Handle server-sent notifications
    while True:
        notification = sess.wait_for_notification()

        # Handle the notification. See the documentation for the
        # `algebraic-data-type` package.
        notification.match(
            request = take_turn,
            field_state = lambda state: print(f'New field state: {state}'),
            event = lambda event: print(f'Event happened: {event}'),
            error = lambda description: print(f'Error: {description}')
        )

# This is where the decision-making part happens.
def take_turn():
    global sess

    # We will always tell our snake to move right.
    action = Action.MOVE(Direction.RIGHT())

    # Send our action to the server
    sess.respond(action)    # May cause an ERR if the move is invalid.
                            # This ERR will appear as the next
                            # ClientNotification. A well-designed client
                            # should handle this situation.
    print('Moved right')

main()
```

(this example is available under the terms of [CC0](https://creativecommons.org/publicdomain/zero/1.0)).

## Low-level API: Messages
Messages play the central role in the protocol. These are units of information
carrying predetermined types of data that can be sent by a client or a server
at any time.

The `message.Message` class represents a message. `Message`s can be serialized
into and deserialized from byte strings via methods `.to_bytes()` and `.from_bytes()`.
This allows to store or transmit them as a sequence of bytes.

This class is an (emulated) [algebraic data type](https://en.wikipedia.org/wiki/Algebraic_data_type).
Python has no built-in capacity for ADTs, but the necessary functionality is provided
by the [`algebraic-data-types`](https://pypi.org/project/algebraic-data-types) package,
so, if you don't understand how `Message`s can be used or constructed,
you may want to consult its documentation.

This particular functionality may not be of a great interest for the users of this
library, so they might want to use the high-level API instead.

## Helper data types
TODO
