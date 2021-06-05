from PyQt5 import QtWidgets, QtGui, QtCore
from client import Client
from ReadyDialog import Ui_ReadyWind
from ReadyWindow import Readywnd
from AdminPage import Ui_AdminPage
from contextlib import ExitStack
from functools import partial
from FirstDialog import Ui_Hello   # импорт нашего сгенерированного файла
import sys
import os
import time
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QLCDNumber, QSlider,
    QVBoxLayout, QApplication)
import threading
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QPushButton, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt

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
        if self.check != 1:
            self.check = 1
            self.changeTitle(0)
        else:
            self.ui.pushButton.setText("Выйти")
            self.close()
    
    def changeTitle(self, param):
        if param == 0:
            self.ui.label.setText("Дождитесь других игроков/окончания игры")
        if param == 1:
            self.ui.label.setText("Поздравляем с победой")
        if param == 2:
            self.ui.label.setText("К сожалению, в этот раз вы проиграли")

class AdminPage(QtWidgets.QDialog):
    
    def __init__(self):
        self.check = 0
        self.tableData = []
        super(AdminPage, self).__init__()
        self.ui = Ui_AdminPage()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.btnClicked)

        self.m = 20
        self.n = 20
        self.plr = 2
        self.time = 1000
        self.turns = 10000

        self.ui.lineEdit.setText("20")
        self.ui.lineEdit_1.setText("20")
        self.ui.Cmd.setText("2")
        self.ui.Cmd_2.setText("1000")
        self.ui.Cmd_3.setText("1000")
        self.ui.Cmd_4.setText("Room1")

        self.addui = Readywnd()

    def btnClicked(self):
        print("ok")
        self.m = self.ui.lineEdit.text()
        self.m = self.ui.lineEdit_1.text()
        self.plr = self.ui.Cmd.text()
        self.time = self.ui.Cmd_2.text()
        self.turns = self.ui.Cmd_3.text()
        self.name = self.ui.Cmd_4.text()

        self.check = 7

        time.sleep(0.25)
        self.changeWindow()


    def changeWindow(self):
        self.addui = Readywnd()
        self.hide()
        self.addui.show()

class App(QWidget):
    something = pyqtSignal()
    
    def connectSignal(self):        
        self.something.connect(self.myAction())

    @QtCore.pyqtSlot()
    def myAction(self):
        self.updateTableData(self.tableData)
        if self.check == 4:
            self.changeInterface()
        if self.check == 6:
            pass
    def changeWindow(self):
        self.addui = Readywnd()
        self.hide()
        self.addui.show()

    def changeInterface(self):
        self.newI = AdminPage()
        self.newI.tableData = self.tableData
        self.newI.check = self.check
        self.hide()
        self.newI.show()
    def __init__(self, tableData: list):
        self.addui = Readywnd()
        self.newI = AdminPage()
        super(QWidget, self).__init__()
        self.roomname = None
        self.table = QTableWidget()
        
        self.table.setColumnCount(1)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.check = 0
        self.tableData = tableData
        # Инициализация таблицы
        self.updateTableData(tableData)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.table)

        buttonsList = QWidget()
        buttonsLayout = QHBoxLayout()
        updateButton = QPushButton("Обновить таблицу")
        connectButton = QPushButton("Присоединиться к комнате")
        createButton = QPushButton("Создать комнату")

        buttonsList.setLayout(buttonsLayout)

        buttonsLayout.addWidget(updateButton)
        buttonsLayout.addWidget(connectButton)
        buttonsLayout.addWidget(createButton)

        # Определение слотов для кнопок при нажатии
        updateButton.clicked.connect(self.updateButtonClick)
        connectButton.clicked.connect(self.connectButtonClick)
        createButton.clicked.connect(self.createButtonClick)

        mainLayout.addWidget(buttonsList)
        self.setLayout(mainLayout)
        self.resize(600, 400)

        
    def updateTableData(self, tableData):
        self.tableData = tableData
        self.table.setRowCount(len(self.tableData))

        for i in range(len(self.tableData)):
            self.table.setItem(i, 0, QTableWidgetItem(self.tableData[i]))

        self.table.resizeColumnToContents(0)

    def updateButtonClick(self):
        self.check = 3
        self.updateTableData(self.tableData)
        pass

    def connectButtonClick(self):
        if (len(self.table.selectedItems()) > 0):
            selectedItem = self.table.selectedItems()[0].text()
            self.roomname = selectedItem
            self.check = 1

            time.sleep(0.25)
            self.changeWindow()

    def createButtonClick(self):
        self.check = 2
        self.changeInterface()
        pass

class mywindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_Hello()
        self.ui.setupUi(self)
        self.check = 0
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
        self.ui.pushButton_2.clicked.connect(self.btnClicked2)
    def btnClicked2(self):
        address  = self.ui.lineEdit.text()
        port = self.ui.lineEdit_1.text()
        name = "@viewer"
        cmd = ""

        cur = Client(address, port, name, cmd)
        self.hide()

        #cur.application = Readywnd()
        #cur.application.show()
        cur.application = App([])
        cur.application.show()


        threading.Thread(target=cur.run_basic_session, daemon=True).start()

    def btnClicked(self):

        address  = self.ui.lineEdit.text()
        port = self.ui.lineEdit_1.text()
        name = self.ui.Pname.text()
        cmd = self.ui.Cmd.text()

        cur = Client(address, port, name, cmd)
        self.hide()

        #cur.application = Readywnd()
        #cur.application.show()
        cur.application = App([])
        cur.application.show()


        threading.Thread(target=cur.run_basic_session, daemon=True).start()
 
app = QtWidgets.QApplication(sys.argv)
application = mywindow()
application.show()
sys.exit(app.exec())
