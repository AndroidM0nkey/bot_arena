from PyQt5 import QtWidgets, QtGui, QtCore
from ReadyDialog import Ui_ReadyWind   # импорт нашего сгенерированного файла
import sys
from bot_arena_proto.data import *
from bot_arena_proto.event import Event
from bot_arena_proto.session import ClientSession, ClientInfo
from game_viewer_files.main_viewer import Viewer
from StreamEditor import StreamEditor
import pygame
import game_viewer_files.config as c
import time
import curio


class Readywnd(QtWidgets.QDialog):
    
    def __init__(self):
        self.check = 0
        super(Readywnd, self).__init__()
        self.ui = Ui_ReadyWind()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.btnClicked)
        self.check = 0

    def btnClicked(self):
        self.check = 1
        print("1")

#for tests
app = QtWidgets.QApplication(sys.argv)
application = Readywnd()
application.show()
sys.exit(app.exec())