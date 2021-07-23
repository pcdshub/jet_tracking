from mainwindow import MainWindow
import sys, os

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from mainwindow import MainWindow
from signals import Signals
from context import Context

"""
def readCSS(fname):

	f = open(fname, 'r')
	s = f.read()
	f.close()

	return s
"""

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    #app.setWindowIcon(QtWidgets.QIcon("images/icon.png"))

    #sys.setrecursionlimit(4096*4096)

    mw = MainWindow()
    mw.show()
    app.exec_()



