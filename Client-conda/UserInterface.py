from PyQt5 import QtWidgets, QtGui, QtCore
from client import Client
from ReadyDialog import Ui_ReadyWind
from ReadyWindow import Readywnd
from contextlib import ExitStack
from functools import partial
from FirstDialog import Ui_Hello   # импорт нашего сгенерированного файла
import sys
import os
import time
 
 
class mywindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_Hello()
        self.ui.setupUi(self)

        #setting up fonts
        self.ui.label.setFont(
            QtGui.QFont('SansSerif', 10)
        )
        self.ui.label.setAlignment(QtCore.Qt.AlignCenter)

        #marking lineEdits
        self.ui.lineEdit.setText("0.0.0.0")
        self.ui.lineEdit_1.setText("23456")
        self.ui.Pname.setText("Player")
        self.ui.Cmd.setText("./curbot")
        self.ui.pushButton.clicked.connect(self.btnClicked)
 
    def btnClicked(self):

        address  = self.ui.lineEdit.text()
        port = self.ui.lineEdit_1.text()
        name = self.ui.Pname.text()
        cmd = self.ui.Cmd.text()

        cur = Client(address, port, name, cmd)
        self.w = Readywnd()
        self.w.show()
        self.hide()

        with ExitStack() as stack:
            stack.callback(cur.run_basic_session)
            
        

        

class Readywnd(QtWidgets.QDialog):
    check = 0

    def __init__(self):
        super().__init__()
        self.ui = Ui_ReadyWind()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.btnClicked)
        

    def btnClicked(self):
        check = 1
 
 
app = QtWidgets.QApplication(sys.argv)
#application = Readywnd()
application = mywindow()
application.show()
 
sys.exit(app.exec())