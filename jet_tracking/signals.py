from PyQt5 import QtCore

class Signals(QtCore.QObject):

    #emitted in thread
    params = QtCore.pyqtSignal(list)
    stopped = QtCore.pyqtSignal()
    
    #emitted in main window
    rdbttnStatus = QtCore.pyqtSignal(int)


