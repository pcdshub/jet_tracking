import numpy as np
from PyQt5 import QtCore


class Signals(QtCore.QObject):
    """
    A class representing various PyQt signals used in the application.
    """

    changeRunLive = QtCore.pyqtSignal(bool)
    """
    Signal emitted to change the run live flag.

    Args:
        bool: Flag indicating if the data stream will come in live. True if live
    """

    changeCalibrationSource = QtCore.pyqtSignal(str)
    """
    Signal emitted to change the calibration source. Can either be in the GUI or from Calibration file

    Args:
        str: The calibration source. Can be either 'calibration in GUI' or 'calibration from results'
    """

    changeNumberCalibration = QtCore.pyqtSignal(int)
    """
    Signal emitted to change the number of values to use for calibration.

    Args:
        int: The new number of calibration points.
    """

    changeScanLimit = QtCore.pyqtSignal(int)
    """
    Signal emitted to change the number of times a scan is allowed to try again after failing.

    Args:
        int: The new scan limit.
    """

    changePercent = QtCore.pyqtSignal(float)
    """
    Signal emitted to change the percentage range of accepted values from the mean.

    Args:
        float: The new percentage value.
    """

    changeDisplayTime = QtCore.pyqtSignal(int, int)
    """
    Signal emitted to change the display time.

    Args:
        int: The display time.
        int: The refresh rate
    """

    setNewXAxis = QtCore.pyqtSignal(int)
    """
    Signal emitted to set a new X-axis range.

    Args:
        int: The index of the first nan value in the new list.
    """

    startMotorThread = QtCore.pyqtSignal()
    """
    Signal emitted to start the motor thread.
    """

    stopMotorThread = QtCore.pyqtSignal(bool)
    """
    Signal emitted to stop the motor thread.

    Args:
        bool: Flag indicating if the motor thread should be stopped immediately.
    """

    intensitiesForMotor = QtCore.pyqtSignal(dict)
    """
    Signal emitted to provide intensities for motor control.

    Args:
        dict: Dictionary containing intensities for motor control.
    """

    valuesRequest = QtCore.pyqtSignal()
    """
    Signal emitted to request values for motor control.
    """

    connectMotor = QtCore.pyqtSignal()
    """
    Signal emitted to establish a connection with the motor.
    """

    liveMotor = QtCore.pyqtSignal(bool)
    """
    Signal emitted to control the motor's live status.

    Args:
        bool: Flag indicating if the motor should be in live mode.
    """

    notifyMotor = QtCore.pyqtSignal(str)
    """
    Signal emitted to notify the motor about a the status of the intensity compared to the mean and stddev.

    Args:
        str: The status to be notified to the motor.
    """

    motorMode = QtCore.pyqtSignal(str)
    """
    Signal emitted to change the motor mode.

    Args:
        str: The new motor mode.
    """

    plotMotorMoves = QtCore.pyqtSignal(float, float, list, list)
    """
    Signal emitted to plot the motor moves.

    Args:
        float: the motor position of max value.
        float: The max value 
        list: List of X-coordinates for the motor moves.
        list: List of Y-coordinates for the motor moves.
    """

    endEarly = QtCore.pyqtSignal()
    """
    Signal emitted to indicate an early termination of a process.
    """

    finishedMotorAlgorithm = QtCore.pyqtSignal()
    """
    Signal emitted to indicate the completion of a motor algorithm. If there is supposed to be a recalibration
    after, then the StatusThread will start calibration at this new position.
    """

    imageProcessing = QtCore.pyqtSignal(dict)
    """
    Signal emitted to perform image processing. The dict contains all of the image morphology values from sliders

    Args:
        dict: Dictionary containing image processing parameters from sliders.
    """

    imageProcessingComplete = QtCore.pyqtSignal(bool)
    """
    Signal emitted to indicate the completion of image processing.

    Args:
        bool: Flag indicating if image processing is complete.
    """

    imageProcessingRequest = QtCore.pyqtSignal(bool)
    """
    Signal emitted to request image processing.

    Args:
        bool: Flag indicating if image processing should be performed.
    """

    initializeCamValues = QtCore.pyqtSignal()
    """
    Signal emitted to initialize camera values.
    """

    linesInfo = QtCore.pyqtSignal(tuple, tuple)
    """
    Signal emitted to provide horizontal and vertical line information for the ROI.

    Args:
        tuple: Tuple containing the position of the upper left corner where the lines meet.
        tuple: Tuple containing the position of the lower right corner where the lines meet.
    """

    startImageThread = QtCore.pyqtSignal()
    """
    Signal emitted to start the image thread.
    """

    stopImageThread = QtCore.pyqtSignal(bool)
    """
    Signal emitted to stop the image thread.

    Args:
        bool: Flag indicating if the image thread should be stopped immediately.
    """

    camImager = QtCore.pyqtSignal(np.ndarray)
    """
    Signal emitted to provide camera image data which is then updated in the jetImageWidget.

    Args:
        np.ndarray: NumPy array containing the camera image data.
    """

    trackingStatus = QtCore.pyqtSignal(str, str)
    """
    Signal emitted to update the tracking status.

    Args:
        str: The name of the tracking algorithm.
        str: The current tracking status.
    """

    comDetection = QtCore.pyqtSignal(bool)
    """
    Signal emitted to enable or disable center-of-mass detection.

    Args:
        bool: Flag indicating if center-of-mass detection should be enabled.
    """
    terminateAll = QtCore.pyqtSignal()
    """
    Signal emitted to terminate all processes and close the application.
    """

    showMessageBox = QtCore.pyqtSignal(str, str)
    """
    Signal emitted to show a message box with the given title and message.

    Args:
        str: Title of the message box.
        str: Message to be displayed.
    """

    # Signal emitted in StatusThread
    changeStatus = QtCore.pyqtSignal(str, str)
    """
    Signal emitted to change the status displayed in the application.

    Args:
        str: Status text.
        str: Associated status color.
    """

    refreshGraphs = QtCore.pyqtSignal(dict, int)
    """
    Signal emitted to refresh the graphs in the GraphsWidget.

    Args:
        dict: Data for updating the graphs.
        int: Refresh rate for updating the graphs.
    """

    startStatusThread = QtCore.pyqtSignal()
    """
    Signal emitted to start the StatusThread.
    """

    stopStatusThread = QtCore.pyqtSignal(bool)
    """
    Signal emitted to stop the StatusThread.

    Args:
        bool: Flag indicating if the status thread should be stopped.
    """

    changeStatusMode = QtCore.pyqtSignal(str)
    """
    Signal emitted to indicate the mode of operation.

    Args:
        str: Mode of operation.
    """

    updateRunValues = QtCore.pyqtSignal(bool)
    """
    Signal emitted to update the run values.

    Args:
        bool: Flag indicating if the run values should be updated.
    """

    message = QtCore.pyqtSignal(str)
    """
    Signal emitted to display a message.

    Args:
        str: Message to be displayed.
    """

    enableTracking = QtCore.pyqtSignal(bool)
    """
    Signal emitted to enable or disable tracking.

    Args:
        bool: Flag indicating if tracking should be enabled.
    """

    changeCalibrationDisplay = QtCore.pyqtSignal()
    """
    Signal emitted to change the calibration display so that the calibration values are displayed.
    """

    changeCalibrationValues = QtCore.pyqtSignal(dict)
    """
    Signal emitted to change the calibration values.

    Args:
        dict: Dictionary containing the calibration values.
    """

    changeCalibrationPriority = QtCore.pyqtSignal(str)
    """
    Signal emitted to change the calibration priority.

    Args:
        str: Calibration priority.
    """

    imageSearch = QtCore.pyqtSignal()
    """
    Signal emitted to initiate an jet search based on the image.

    This signal does not require any arguments. It is emitted when there is a need to initiate an image search process. The connected slots can listen to this signal and perform the necessary actions related to image searching.
    """

    changeMotorPosition = QtCore.pyqtSignal(float)
    """
    Signal emitted to change the motor position.

    Args:
        float: The new motor position.
    """

    changeReadPosition = QtCore.pyqtSignal(float)
    """
    Signal emitted to change the read position.

    Args:
        float: The new read position.
    """

    changeDroppedShots = QtCore.pyqtSignal(float)
    """
    Signal emitted to change the number of dropped shots.

    Args:
        float: The new number of dropped shots.
    """

    changePeakIntensity = QtCore.pyqtSignal(float)
    """
    Signal emitted to change the peak intensity.

    Args:
        float: The new peak intensity value.
    """

    changeJetRadius = QtCore.pyqtSignal(float)
    """
    Signal emitted to change the jet radius.

    Args:
        float: The new jet radius value.
    """

    changeJetCenter = QtCore.pyqtSignal(float)
    """
    Signal emitted to change the jet center position.

    Args:
        float: The new jet center position.
    """

    changeMaxIntensity = QtCore.pyqtSignal(float)
    """
    Signal emitted to change the maximum intensity value.

    Args:
        float: The new maximum intensity value.
    """

    changeBackground = QtCore.pyqtSignal(float)
    """
    Signal emitted to change the background intensity value.

    Args:
        float: The new background intensity value.
    """







