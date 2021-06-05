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
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QLCDNumber, QSlider,
    QVBoxLayout, QApplication)
import threading
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QPushButton, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt

class App(QWidget):
    something = pyqtSignal()
    
    def connectSignal(self):        
        self.something.connect(self.myAction())

    @QtCore.pyqtSlot()
    def myAction(self):
        print("hello")
        self.updateTableData(self.tableData)
    def __init__(self, tableData: list):
        super(QWidget, self).__init__()
        self.roomname = None
        self.table = QTableWidget()
        
        self.table.setColumnCount(1)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.check = 0
        self.tableData = []
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
        # self.updateTable(tbl.getTable())
        pass

    def connectButtonClick(self):
        if (len(self.table.selectedItems()) > 0):
            selectedItem = self.table.selectedItems()[0].text()
            self.roomname = selectedItem
            self.check = 1

    def createButtonClick(self):
        self.check = 2
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
