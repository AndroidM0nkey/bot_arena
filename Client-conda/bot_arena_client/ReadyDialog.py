# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ReadyDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ReadyWind(object):
    def setupUi(self, ReadyWind):
        ReadyWind.setObjectName("ReadyWind")
        ReadyWind.resize(240, 320)
        self.pushButton = QtWidgets.QPushButton(ReadyWind)
        self.pushButton.setGeometry(QtCore.QRect(10, 283, 221, 31))
        self.pushButton.setObjectName("pushButton")
        self.label = QtWidgets.QLabel(ReadyWind)
        self.label.setGeometry(QtCore.QRect(10, 20, 221, 111))
        self.label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label.setScaledContents(False)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")

        self.retranslateUi(ReadyWind)
        QtCore.QMetaObject.connectSlotsByName(ReadyWind)

    def retranslateUi(self, ReadyWind):
        _translate = QtCore.QCoreApplication.translate
        ReadyWind.setWindowTitle(_translate("ReadyWind", "Dialog"))
        self.pushButton.setText(_translate("ReadyWind", "Готов!"))
        self.label.setText(_translate("ReadyWind", "Нажмите готов, когда все игроки подключатся и будут готовы начать"))