from PyQt5 import QtCore

class Signals(QtCore.QObject):

    #emitted in thread
    params = QtCore.pyqtSignal(list)
    stopped = QtCore.pyqtSignal()
    
    #emitted in main window
    rdbttnStatus = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(int) # 0 - no tracking, 1 - tracking, 2 - warning, low incoming beam intensity, 3 - warning, may have lost jet
    sigma = QtCore.pyqtSignal(float)
    nsamp = QtCore.pyqtSignal(float)

    #calibration
    ali0 = QtCore.pyqtSignal(float)
    calibration = QtCore.pyqtSignal()
