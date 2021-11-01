from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QFrame
from datastream import StatusThread, MotorThread
from gui.widgets.controlWidgetUi import Controls_Ui
import logging
import matplotlib.pyplot as plt

log = logging.getLogger(__name__)


class ControlsWidget(QFrame, Controls_Ui):

    def __init__(self, context, signals):
        super(ControlsWidget, self).__init__()
        log.info("Main Thread: %d" % QThread.currentThreadId())
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.initialize_threads()
        self.set_thread_options()
        self.set_motor_options()
        self.make_connections()

    def initialize_threads(self):
        self.worker_status = StatusThread(self.context, self.signals)
        self.worker_motor = MotorThread(self.context, self.signals)

    def set_thread_options(self):
        self.le_percent.setText(str(self.context.percent))
        self.le_ave_graph.setText(str(self.context.graph_ave_time))
        self.le_refresh_rate.setText(str(self.context.refresh_rate))
        self.le_x_axis.setText(str(self.context.display_time))

    def set_motor_options(self):
        self.le_motor_ll.setText(str(self.context.low_limit))
        self.le_motor_hl.setText(str(self.context.high_limit))
        self.le_size.setText(str(self.context.step_size))
        self.cbox_algorithm.setCurrentText(self.context.algorithm)

    def make_connections(self):

        self.le_percent.checkVal.connect(self.context.update_percent)
        self.le_refresh_rate.checkVal.connect(self.context.update_refresh_rate)
        self.le_ave_graph.checkVal.connect(self.context.update_graph_averaging)
        self.le_motor_ll.checkVal.connect(self.update_limits)
        self.le_motor_hl.checkVal.connect(self.update_limits)
        self.le_x_axis.checkVal.connect(self.context.update_display_time)
        self.le_size.checkVal.connect(self.context.update_step_size)
        self.le_ave_motor.checkVal.connect(self.context.update_motor_averaging)
        self.cbox_algorithm.currentTextChanged.connect(self.context.update_algorithm)
        self.bttngrp1.buttonClicked.connect(self.checkBttn)
        self.bttngrp2.buttonClicked.connect(self.checkBttn)
        self.bttngrp3.buttonClicked.connect(self.checkBttn)

        self.bttn_connect_motor.clicked.connect(self.context.connect_motor)
        self.bttn_search.clicked.connect(self._start_motor)
        self.bttn_tracking.clicked.connect(self._enable_tracking)
        self.bttn_stop_motor.clicked.connect(self._stop_motor)
        self.signals.trackingStatus.connect(self.set_tracking_status)

        self.signals.changeStatus.connect(self.set_monitor_status)
        self.signals.changeCalibrationDisplay.connect(self.set_calibration)

        self.signals.wakeMotor.connect(self._start_motor)
        self.signals.sleepMotor.connect(self._stop_motor)
        self.signals.message.connect(self.receive_message)

        self.bttn_stop.clicked.connect(self._stop)
        self.bttn_calibrate.clicked.connect(self._calibrate)
        self.bttn_start.clicked.connect(self.start_processes)

        self.signals.plotMotorMoves.connect(self.plot_motor_moves)

    def start_processes(self):
        self.worker_status.start()

    def _stop(self):
        if self.worker_motor.isRunning():
            self.worker_motor.requestInterruption()
            self.worker_motor.wait()
        if self.worker_status.isRunning():
            self.worker_status.requestInterruption()
            self.worker_status.wait()

    def _calibrate(self):
        if not self.worker_status.isRunning():
            self.text_area.append("You are not running so there's \
                  nothing to calibrate.. hit start first")
        else:
            self.context.set_mode("calibrate")

    def _enable_tracking(self):
        self.set_tracking_status("enabled", green)
        self.context.update_tracking(True)

    def _start_motor(self):
        if not self.worker_motor.isRunning():
            if self.worker_status.isRunning():
                self.worker_motor.start()
            else:
                self.signals.message.emit("You must start getting points first!")
        else:
            if not self.worker_motor.isInterruptionRequested():
                self.worker_motor.start()
            else:
                self.signals.message.emit("The motor is already running")

    def _stop_motor(self):
        if self.worker_motor.isRunning():
            self.worker_motor.requestInterruption()
            self.worker_motor.wait()
        if self.sender() is self.bttn_stop_motor:
            self.context.set_tracking(False)
            self.set_tracking_status('disabled', red)

    def plot_motor_moves(self, position, maximum, positions, intensities):
        fig = plt.figure()
        plt.xlabel('motor position')
        plt.ylabel('I/I0 intensity')
        plt.plot(position, maximum, 'ro')
        x = positions
        y = intensities
        plt.scatter(x, y)
        plt.show()

    def set_calibration(self):
        """
        this function is called when a successful calibration is ran. It updates the display.
        """
        self.lbl_i0_status.display(self.context.calibration_values['i0']['mean'])
        self.lbl_diff_status.display(self.context.calibration_values['diff']['mean'])

    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            widgetToRemove = layout.itemAt(i).widget()
            layout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

    def set_tracking_status(self, status, color):
        self.lbl_tracking_status.setText(status)
        self.lbl_tracking_status.setStyleSheet(f"\
                background-color: {color};")

    def set_monitor_status(self, status, color):
        self.lbl_monitor_status.setText(status)
        self.lbl_monitor_status.setStyleSheet(f"\
                background-color: {color};")

    def cleanup_correction(self):
        self.worker_motor = None

    def receive_status(self, status):
        if status == 'outside':
            if self.correction_thread is None:
                # avoid issues with fluctuations and multiple corrections
                self.correction_thread = correctionThread()
                self.correction_thread.finished.connect(self.cleanup_correction)
                self.correction_thread.start()

    def update_limits(self, limit):
        self.context.update_limits(float(self.le_motor_hl.text()), float(self.le_motor_ll.text()))

    def receive_message(self, message):
        pt = self.text_area.toPlainText()
        if pt.split('\n')[-1] == message.split('\n')[-1]:
            pass
        else:
            self.text_area.append(message)

    def checkBttn(self, button):
        bttn = button.text()
        if bttn == "simulated data":
            self.rdbttn_manual.click()
            self.rdbttn_auto.setEnabled(False)
            self.context.update_live_graphing(False)
        elif bttn == "live data":
            self.rdbttn_auto.setEnabled(True)
            self.context.update_live_graphing(True)
        elif bttn == "manual \nmotor moving":
            self.bttn_search.setEnabled(True)
            self.bttn_tracking.setEnabled(False)
            self.bttn_stop_motor.setEnabled(False)
            self.context.update_manual_motor(True)
        elif bttn == "automated \nmotor moving":
            self.bttn_search.setEnabled(True)
            self.bttn_tracking.setEnabled(True)
            self.bttn_stop_motor.setEnabled(True)
            self.context.update_manual_motor(False)
        elif bttn == "calibration in GUI":
            self.context.update_calibration_source(bttn)
        elif bttn == "calibration from results":
            self.context.update_calibration_source(bttn)

    def setDefaultStyleSheet(self):
        # This should be done with a json file

        self.setStyleSheet("\
            Label {\
                qproperty-alignment: AlignCenter;\
                border: 1px solid #FF17365D;\
                border-top-left-radius: 15px;\
                border-top-right-radius: 15px;\
                background-color: #FF17365D;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                max-height: 35px;\
                font-size: 14px;\
            }")
