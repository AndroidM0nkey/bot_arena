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
        self.ui.label.setFont(
            QtGui.QFont('SansSerif', 10)
        )
        self.ui.label.setAlignment(QtCore.Qt.AlignCenter)
        #self.ui.label.setText("Нажмите готов, когда все игроки подключатся и будут готовы начать")
        self.check = 0

    def btnClicked(self):
        self.check = 1
        self.changeTitle(0)
        #print("1")
    
    def changeTitle(self, param):
        if param == 0:
            self.ui.label.setText("Дождитесь других игроков/окончания игры")
        if param == 1:
            self.ui.label.setText("Поздравляем с победой")
        if param == 2:
            self.ui.label.setText("К сожалению, в этот раз вы проиграли")

#for tests
"""
app = QtWidgets.QApplication(sys.argv)
application = Readywnd()
application.show()
sys.exit(app.exec())
"""