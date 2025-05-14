import Drone_color_carte_dynamiquement as dccd
import Interface_graphique as ig
import SQL
import sys
from PyQt5 import QtGui, QtCore, QtWidgets, uic

class Mon_Application(QtWidgets.QMainWindow, ig.Ui_Interface):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = ig.Ui_Interface()
        self.ui.setupUi(self)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Mon_Application()
    window.show()
    app.exec_()