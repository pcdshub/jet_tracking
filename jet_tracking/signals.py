from PyQt5 import QtCore


class Signals(QtCore.QObject):

    # emitted in thread
    status = QtCore.pyqtSignal(str, str)
    buffers = QtCore.pyqtSignal(list)
    avevalues = QtCore.pyqtSignal(dict)
    calibration_values = QtCore.pyqtSignal(dict)
    run_live = QtCore.pyqtSignal(int)

    # emitted in main window
    rdbttn_status = QtCore.pyqtSignal(int)
    sigmaval = QtCore.pyqtSignal(float)
    nsampval = QtCore.pyqtSignal(float)

    # calibration
    ali0 = QtCore.pyqtSignal(float)
    calibration = QtCore.pyqtSignal()
