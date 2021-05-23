from PyQt5 import QtWidgets, QtGui, QtCore
from client import Client
from FirstDialog import Ui_Hello   # импорт нашего сгенерированного файла
import sys
 
 
class mywindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(mywindow, self).__init__()
        self.ui = Ui_Hello()
        self.ui.setupUi(self)

        #setting up fonts
        self.ui.label.setFont(
            QtGui.QFont('SansSerif', 12)
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
        self.close()
        cur.run_basic_session()
        


 
 
app = QtWidgets.QApplication([])
application = mywindow()
application.show()
 
sys.exit(app.exec())