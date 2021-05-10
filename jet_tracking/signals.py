from PyQt5 import QtCore


class Signals(QtCore.QObject):

    # emitted in thread
    status = QtCore.pyqtSignal(str, str)
    buffers = QtCore.pyqtSignal(dict)
    avevalues = QtCore.pyqtSignal(dict)
    calibration_value = QtCore.pyqtSignal(dict)
    run_live = QtCore.pyqtSignal(int)
    mode = QtCore.pyqtSignal(str)
    message = QtCore.pyqtSignal(str)
    tol = QtCore.pyqtSignal(float)
    limits = QtCore.pyqtSignal(float, float)

    # emitted in main window
    rdbttn_status = QtCore.pyqtSignal(int)
    sigmaval = QtCore.pyqtSignal(float)
    nsampval = QtCore.pyqtSignal(float)
    motormove = QtCore.pyqtSignal(int)
    samprate = QtCore.pyqtSignal(float)
    
    # calibration
    ali0 = QtCore.pyqtSignal(float)
    calibration = QtCore.pyqtSignal()

    # motor
    motorPV = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(dict)
    update_calibration = QtCore.pyqtSignal(str, float)
