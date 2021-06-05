from bot_arena_client.StreamEditor import StreamEditor
from bot_arena_client.game_viewer_files import config as c
from bot_arena_client.game_viewer_files.main_viewer import Viewer

import time
import sys
import threading
from functools import partial

import curio
import pygame
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from bot_arena_proto.data import *
from bot_arena_proto.event import Event
from bot_arena_proto.session import ClientSession, ClientInfo

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

        self.handler = Viewer()
        self.score = None

    def run_basic_session(self):
        #app = QtWidgets.QApplication(sys.argv)
        """
        self.application=Readywnd()
        self.application.show()
        """
        curio.run(self.main)
        self.application.hide()

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

        rooms_list = await self.sess.list_rooms()
        room_names = []
        for i in rooms_list:
            room_names.append(i.name)

        #await threading.Thread(target=room_interface, args=(room_names), daemon=True).start()
        self.application.tableData = room_names
        self.application.updateTableData(self.application.tableData)
        self.application.something.emit()

        while True:
            if self.application.check == 1:
                self.application.check = 5
                await self.sess.enter_room(self.application.roomname, None)
                break
            if self.application.check == 2:
                self.application.check = 4
                await self.sess.enter_any_room()
                break
            if self.application.check == 3:
                rooms_list = await self.sess.list_rooms()
                room_names = []
                for i in rooms_list:
                    room_names.append(i.name)
                self.application.tableData = room_names
                self.application.check = 0
                self.application.something.emit()
            await curio.sleep(1)

        #await self.sess.enter_any_room()
        room_properties = await self.sess.get_room_properties()
        if room_properties["open"] != RoomOpenness.OPEN():
            await self.sess.set_room_properties({"open": RoomOpenness.OPEN()})
            print(f'Created room {room_properties["name"]}')
        else:
            print(f'Joined room {room_properties["name"]}')
        if self.application.check == 4:
            self.application.something.emit()
            chck = 0
            admlist = await self.sess.get_room_properties()
            for i in admlist['admins']:
                if i == self.name:
                    chck = 1
                    break
            if chck == 1:
                while True:
                    if self.application.newI.check == 7:
                        d = {}
                        d['name'] = self.application.newI.name
                        d['field_height'] = int(self.application.newI.m)
                        d['field_width'] = int(self.application.newI.n)
                        d['min_players'] = int(self.application.newI.plr)
                        d['turn_timeout_seconds'] = float(self.application.newI.time)
                        d['max_turns'] = int(self.application.newI.turns)
                        await self.sess.set_room_properties(d)
                        break
                    await curio.sleep(1)
            self.application.check = 5
            while True:
                if self.application.newI.addui.check == 1:
                    break
                await curio.sleep(1)
        else:
            while True:
                if self.application.addui.check == 1:
                    break
                await curio.sleep(1)


        await self.sess.ready()
        print("ready for game")
        game_info = await self.sess.wait_until_game_started()

        # Important data
        self.f_width = game_info.field_width
        self.f_height = game_info.field_height

        if self.name == "@viewer":
            self.cell_width = int(c.screen_width / max(self.f_height, self.f_width))
            pygame.init()
            pygame.display.set_caption('Pythons')
            self.screen = pygame.display.set_mode((self.f_width * self.cell_width, self.f_height * self.cell_width))


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
        if self.name == "@viewer":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit(0)
            self.handler.get_message_and_display(self.curField, self.f_height, self.f_width, self.score, self.screen)
        #pygame.init()
        #main_surface = pygame.display.set_mode((c.screen_width, c.screen_width))
        #pygame.display.set_caption('Pythons')
        #get_message_and_display(curField, main_surface)
        #time.sleep(1000)



    async def handle_event(self,event):
        if self.name == "@viewer":
                if event.name == 'GameScoreChanged':
                    self.score = event.data
                    return
                if event.name == 'GameFinished':
                    self.handler.get_message_and_display(self.handler.get_last_fieldstate(), self.handler.get_height(),
                                                        self.handler.get_width(), self.handler.get_score(), self.screen, event.data)
                    while True:
                        if pygame.event.wait().type == pygame.QUIT:
                            exit(0)
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
