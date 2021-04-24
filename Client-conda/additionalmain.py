from bot_arena_proto.data import *
from bot_arena_proto.event import Event
from bot_arena_proto.session import ClientSession, ClientInfo
from game_viewer_files.main_viewer import get_message_and_display
from bot import Bot
import pygame
import game_viewer_files.config as c
import time


# A library that can run async functions.
# Standard `asyncio` can also be used, although with some tweaks.
# (needs `curio` package installed)
import curio

# Session, shared between functions.
# A properly designed program should probably avoid
# using global variables, but this is just a tiny example.
sess = None
curField = None
f_width = 0
f_height = 0
name = 'second'

async def main():
    global sess
    global curField
    global f_height
    global f_width
    global name

    # Connect to the server, assuming it is listening on 127.0.0.1:1234.
    socket = await curio.open_connection(host='0.0.0.0', port=23456)

    # We need an object with read/write methods. In curio, sockets have
    # recv/send methods, and streams have read/write methods. Hence, we need
    # to convert the socket to a stream. Consult the documentation
    # (https://curio.readthedocs.io/en/latest/reference.html#networking)
    # for details.
    stream = socket.as_stream()

    # [[[ Interesting things start here ]]]

    # Create a ClientSession
    client_info = ClientInfo(name)
    sess = ClientSession(stream=stream, client_info=client_info)

    # Perform the handshake
    await sess.initialize()

    await sess.enter_any_room()
    room_properties = await sess.get_room_properties()
    if room_properties["open"] != RoomOpenness.OPEN():
        await sess.set_room_properties({"open": RoomOpenness.OPEN()})
        print(f'Created room {room_properties["name"]}')
    else:
        print(f'Joined room {room_properties["name"]}')

    input('Press Enter when you are ready to start. ')

    # Start the game
    await sess.ready()
    game_info = await sess.wait_until_game_started()

    # Important data
    f_width = game_info.field_width
    f_height = game_info.field_height

    # Handle server-sent notifications
    while True:
        notification = await sess.wait_for_notification()

        # Handle the notification. See the documentation for the
        # `algebraic-data-type` package.
        #
        # Note: the functions `take_turn`, `handle_new_field_state`, `handle_event`
        # and `handle_error` are async, and the result of the `.match()` method
        # is awaited. This is correct and probably the only way to combine pattern
        # matching with asynchronous IO because the following actually happens:
        #
        # (1) `.match()` method calls (but does not await) one of these four functions.
        # (2) This function returns a `coroutine` object, which can be awaited.
        # (3) This object is the value returned from `.match()`.
        # (4) This object is then awaited.
        await notification.match(
            request = take_turn,
            field_state = handle_new_field_state,
            event = handle_event,
            error = handle_error,
        )

async def handle_new_field_state(state):
    # Do something when a new field state arrives.
    # Let's update your current field
    #
    global sess
    global curField
    global f_height
    global f_width
    global name
    curField = state
    #pygame.init()
    #main_surface = pygame.display.set_mode((c.screen_width, c.screen_width))
    #pygame.display.set_caption('Pythons')
    #get_message_and_display(curField, main_surface)
    #time.sleep(1000)



async def handle_event(event):
    # Do something when an event happens.
    #print(f'Event happened: {event}')
    pass

async def handle_error(description):
    print(description)
    # Do something when an error happens.
    #print(f'Error: {description}')
    pass

# This is where the decision-making part happens.
async def take_turn():
    # Tell the server what to do in your turn.
    global sess
    global curField
    global f_height
    global f_width
    global name

    # We will always tell our snake to move right.
    curBot = Bot()
    action = Action.MOVE(curBot.find_direction(curField, f_width, f_height, name))
    #action = Action.MOVE(Direction.UP())
    # Send our action to the server
    await sess.respond(action)  # May cause an ERR if the move is invalid.
                                # This ERR will appear as the next
                                # ClientNotification. A well-designed client
                                # should handle this situation.
    #print('Moved right')

curio.run(main)
