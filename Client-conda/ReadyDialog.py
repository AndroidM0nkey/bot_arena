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
        self.pushButton.setGeometry(QtCore.QRect(30, 270, 171, 34))
        self.pushButton.setObjectName("pushButton")
        self.label = QtWidgets.QLabel(ReadyWind)
        self.label.setGeometry(QtCore.QRect(70, 50, 58, 18))
        self.label.setObjectName("label")

        self.retranslateUi(ReadyWind)
        QtCore.QMetaObject.connectSlotsByName(ReadyWind)

    def retranslateUi(self, ReadyWind):
        _translate = QtCore.QCoreApplication.translate
        ReadyWind.setWindowTitle(_translate("ReadyWind", "Dialog"))
        self.pushButton.setText(_translate("ReadyWind", "PushButton"))
        self.label.setText(_translate("ReadyWind", "TEST"))
