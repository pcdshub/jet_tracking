from PyQt5 import QtCore


class Signals(QtCore.QObject):

    # emitted in thread
    status = QtCore.pyqtSignal(str, str)
    buffers = QtCore.pyqtSignal(dict)
    avevalues = QtCore.pyqtSignal(dict)
    calibration_value = QtCore.pyqtSignal(dict)
    run_live = QtCore.pyqtSignal(int)
    mode = QtCore.pyqtSignal(str)

    # emitted in main window
    rdbttn_status = QtCore.pyqtSignal(int)
    sigmaval = QtCore.pyqtSignal(float)
    nsampval = QtCore.pyqtSignal(float)
    motormove = QtCore.pyqtSignal(int)

    # calibration
    ali0 = QtCore.pyqtSignal(float)
    calibration = QtCore.pyqtSignal()
