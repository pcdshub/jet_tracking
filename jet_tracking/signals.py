import numpy as np
from PyQt5 import QtCore
from PyQt5.QtGui import QImage


class Signals(QtCore.QObject):

    # emit in StatusThread
    # connect in ControlsWidget
    changeStatus = QtCore.pyqtSignal(str, str)
    # emit in StatusThread
    # connect in GraphsWidget
    refreshGraphs = QtCore.pyqtSignal(dict)
    # emit in StatusThread
    # connect in GraphsWidget
    refreshAveValueGraphs = QtCore.pyqtSignal(dict)
    # emit in ControlsWidget
    # connect in StatusThread
    mode = QtCore.pyqtSignal(str)
    # emit in StatusThread
    # connect in StatusThread
    message = QtCore.pyqtSignal(str)
    # emit in StatusThread
    # connect in GraphsWidget
    changeDisplayFlag = QtCore.pyqtSignal(str)
    # emit in Context
    # connect in StatusThread
    enableTracking = QtCore.pyqtSignal(bool)
    # emit in GraphsWidget
    # connect in ControlsWidget
    changeCalibrationDisplay = QtCore.pyqtSignal()
    # emit in StatusThread
    # connect in GraphsWidget
    changeCalibrationValues = QtCore.pyqtSignal(dict)
    # emit in Context
    # connect in ValueReader
    changeRunLive = QtCore.pyqtSignal(bool)
    # emit in Context
    # connect in StatusThread
    changeCalibrationSource = QtCore.pyqtSignal(str)
    # emit in Context
    # connect in StatusThead
    changePercent = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in
    changeGraphAve = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in
    changeRefreshRate = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in
    changeDisplayTime = QtCore.pyqtSignal(int)
    # emit in Context
    # connect in
    changeManual = QtCore.pyqtSignal(bool)
    # emit in Context
    # connect in
    changeMotorLimits = QtCore.pyqtSignal(float, float)
    # emit in Context
    # connect in
    changeStepSize = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in
    changeMotorAveraging = QtCore.pyqtSignal(float)
    # emit in statusthread
    # connect in motorthread
    intensitiesForMotor = QtCore.pyqtSignal(dict)
    # emit in motorthread
    # connect in statusthread
    valuesRequest = QtCore.pyqtSignal()
    # emit in context
    # connect in motorthread
    connectMotor = QtCore.pyqtSignal()
    # emit in context
    # connect in motorthread
    liveMotor = QtCore.pyqtSignal(bool)
    # emit in statusthread
    # connect in motorthread
    notifyMotor = QtCore.pyqtSignal(str)
    # emit in context
    # connect in motorthread
    motorMode = QtCore.pyqtSignal(str)
    # emit in motorthread
    # connect in controlwidget
    plotMotorMoves = QtCore.pyqtSignal(float, float, list, list)
    # emit in controlWidget
    # connect in all motor algorithms
    endEarly = QtCore.pyqtSignal()
    # emit in editorwidget
    # connect in jetimagefeed
    imageProcessing = QtCore.pyqtSignal(dict)
    # emit in motorthread
    # connect in jetimageaction
    imageProcessingRequest = QtCore.pyqtSignal(float)
    # emit in jetImageAction
    # connect in motorthread
    imageProcessingComplete = QtCore.pyqtSignal()

    # added when adding simulator
    update = QtCore.pyqtSignal(dict)
    changeMotorPosition = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in num_gen
    changeDroppedShots = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in num_gen
    changePeakIntensity = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in num_gen
    changeJetRadius = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in num_gen
    changeJetCenter = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in num_gen
    changeMaxIntensity = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in num_gen
    changeBackground = QtCore.pyqtSignal(float)
    # emit in Context
    # connect in num_gen
    changeAlgorithm = QtCore.pyqtSignal(str)
    # emit in GraphsWidget
    # connect in StatusThread
    changeAverageSize = QtCore.pyqtSignal(int)
    # emit in context
    # connect in datastream
    connectCam = QtCore.pyqtSignal()
    # emit in jetimagefeed
    # connect in jetimagewidget
    camImage = QtCore.pyqtSignal(QImage)
    # emit in editorWidget
    # connect in jetImageWidget
    updateImage = QtCore.pyqtSignal(np.ndarray)
    # emit in simcontrolwidget
    # connect in controlwidget
    trackingStatus = QtCore.pyqtSignal(str, str)
