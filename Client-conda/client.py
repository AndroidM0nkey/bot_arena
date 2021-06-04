from bot_arena_proto.data import *
from bot_arena_proto.event import Event
from bot_arena_proto.session import ClientSession, ClientInfo
from ReadyWindow import Readywnd
from game_viewer_files.main_viewer import Viewer
from StreamEditor import StreamEditor
#from bot import Bot
import pygame
import game_viewer_files.config as c
import time
import curio
import sys
from PyQt5 import QtWidgets, QtGui, QtCore


class Client:
    def __init__(self, address, port, name, cmd):
        self.host = address
        self.port = port
        self.name = name
        self.cmd = cmd

        #
        sess = None
        curField = None
        f_width = 0
        f_height = 0
        self.application = None

    def run_basic_session(self):
        #app = QtWidgets.QApplication(sys.argv)
        curio.run(self.main)
       

    async def main(self):

        # Connect to the server, assuming it is listening on 127.0.0.1:1234.
        socket = await curio.open_connection(host=self.host, port=self.port)

        # We need an object with read/write methods. In curio, sockets have
        # recv/send methods, and streams have read/write methods. Hence, we need
        # to convert the socket to a stream. Consult the documentation
        # (https://curio.readthedocs.io/en/latest/reference.html#networking)
        # for details.
        stream = socket.as_stream()

        # [[[ Interesting things start here ]]]

        # Create a ClientSession
        client_info = ClientInfo(self.name)
        self.sess = ClientSession(stream=stream, client_info=client_info)

        # Perform the handshake
        await self.sess.initialize()

        await self.sess.enter_any_room()
        room_properties = await self.sess.get_room_properties()
        if room_properties["open"] != RoomOpenness.OPEN():
            await self.sess.set_room_properties({"open": RoomOpenness.OPEN()})
            print(f'Created room {room_properties["name"]}')
        else:
            print(f'Joined room {room_properties["name"]}')

        # Start the game
        
        #app2 = QtWidgets.QApplication([])
        """
        while(self.application.check == 1):
            time.sleep(0.1) 
        """

        await self.sess.ready()
        game_info = await self.sess.wait_until_game_started()

        # Important data
        self.f_width = game_info.field_width
        self.f_height = game_info.field_height

        # Handle server-sent notifications
        while True:
            notification = await self.sess.wait_for_notification()

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
                request = self.take_turn,
                field_state = self.handle_new_field_state,
                event = self.handle_event,
                error = self.handle_error,
            )

    async def handle_new_field_state(self,state):
        # Do something when a new field state arrives.
        # Let's update your current field
        #
        self.curField = state
        #pygame.init()
        #main_surface = pygame.display.set_mode((c.screen_width, c.screen_width))
        #pygame.display.set_caption('Pythons')
        #get_message_and_display(curField, main_surface)
        #time.sleep(1000)



    async def handle_event(self,event):
        # TODO: replace it with something that can be handled by the calling code.
        if event.name == 'GameFinished':
            exit()

    async def handle_error(self,description):
        print(description)
        # Do something when an error happens.
        #print(f'Error: {description}')
        pass

    # This is where the decision-making part happens.
    async def take_turn(self):
        # Tell the server what to do in your turn.
        # We will always tell our snake to move right.
        #curBot = Bot()
        #action = Action.MOVE(curBot.find_direction(curField, f_width, f_height, name))
        cur_test = StreamEditor(self.name, self.cmd)
        move = cur_test.call_bot(self.f_height, self.f_width, self.curField)
        action = None
        if move == "0\n":
            action = Action.MOVE(Direction.DOWN())
        if move == "1\n":
            action = Action.MOVE(Direction.RIGHT())
        if move == "2\n":
            action = Action.MOVE(Direction.UP())
        if move == "3\n":
            action = Action.MOVE(Direction.LEFT())
        #action = Action.MOVE(Direction.UP())
        # Send our action to the server
        await self.sess.respond(action)  # May cause an ERR if the move is invalid.
                                    # This ERR will appear as the next
                                    # ClientNotification. A well-designed client
                                    # should handle this situation.
        #print('Moved right')
