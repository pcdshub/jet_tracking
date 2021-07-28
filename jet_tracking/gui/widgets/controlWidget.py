from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QFrame
from datastream import StatusThread, MotorThread
from gui.widgets.controlWidgetUi import Controls_Ui
import logging

log = logging.getLogger(__name__)


class ControlsWidget(QFrame, Controls_Ui):

    def __init__(self, context, signals):
        super(ControlsWidget, self).__init__()
        log.info("Main Thread: %d" % QThread.currentThreadId())
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.set_thread_options()
        self.set_motor_options()
        self._start()

    def set_thread_options(self):
        self.context.thread_options['live graphing'] = self.bttngrp1.checkedId()
        self.context.thread_options['calibration source'] = self.bttngrp3.checkedId()
        self.context.thread_options['percent'] = float(self.le_percent.text())
        self.context.thread_options['averaging'] = float(self.le_ave_graph.text())
        self.context.thread_options['sampling rate'] = float(self.le_refresh_rate.text())
        self.context.thread_options['manual motor'] = self.bttngrp2.checkedId()

    def set_motor_options(self):
        self.context.motor_options['high limit'] = float(self.le_motor_hl.text())
        self.context.motor_options['low limit'] = float(self.le_motor_ll.text())
        self.context.motor_options['step size'] = float(self.le_size.text())
        self.context.motor_options['averaging'] = float(self.le_ave_motor    .text())
        self.context.motor_options['algorithm'] = self.cbox_algorithm.currentIndex()

    def _start(self):
        self.worker_status = StatusThread(self.context, self.signals)
        self.worker_motor = MotorThread(self.context, self.signals)

        self.le_percent.checkVal.connect(self.update_percent)
        self.le_refresh_rate.checkVal.connect(self.update_refresh_rate)
        self.le_ave_graph.checkVal.connect(self.update_nsamp)
        self.le_motor_ll.checkVal.connect(self.update_limits)
        self.le_motor_hl.checkVal.connect(self.update_limits)
        self.le_size.checkVal.connect(self.update_tol)
        self.bttngrp1.buttonClicked.connect(self.checkBttn)
        self.bttngrp2.buttonClicked.connect(self.checkBttn)
        self.bttngrp3.buttonClicked.connect(self.checkBttn)

        self.bttn_search.clicked.connect(self._start_motor)
        self.bttn_tracking.clicked.connect(self._enable_tracking)
        self.bttn_stop_motor.clicked.connect(self._stop_motor)

        self.signals.status.connect(self.update_monitor_status)
        self.signals.display_calibration.connect(self.update_calibration)

        self.signals.wake.connect(self._start_motor)
        self.signals.sleep.connect(self._stop_motor)
        self.signals.message.connect(self.receive_message)

        self.bttn_stop.clicked.connect(self._stop)
        self.bttn_calibrate.clicked.connect(self._calibrate)
        self.bttn_start.clicked.connect(self.worker_status.start)

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
        self.update_tracking_status("enabled", green)
        self.context.set_tracking(True)
        self._start_motor()

    def _start_motor(self):
        if not self.worker_motor.isRunning():
            if self.worker_status.isRunning():
                self.context.set_mode("correcting")
                self.worker_motor.start()
            else:
                self.text_area.append("there's nothing to scan!")
        else:
            if not self.worker_motor.isInterruptionRequested():
                self.worker_motor.start()
            else:
                self.text_area.append("The motor is already running")

    def _stop_motor(self):
        if self.worker_motor.isRunning():
            self.worker_motor.requestInterruption()
            self.worker_motor.wait()
        if self.sender() is self.bttn_stop_motor:
            self.context.set_tracking(False)
            self.update_tracking_status('disabled', red)

    def update_calibration(self):
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

    def update_tracking_status(self, status, color):
        self.lbl_tracking_status.setText(status)
        self.lbl_tracking_status.setStyleSheet(f"\
                background-color: {color};")

    def update_monitor_status(self, status, color):
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

    def update_percent(self, percent):
        self.context.update_thread_options('status', 'percent', percent)
        if self.context.calibrated:
            self.context.set_mode('calibrate')

    def update_nsamp(self, nsamp):
        self.context.update_thread_options('status', 'average', nsamp)

    def update_refresh_rate(self, rrate):
        self.context.update_thread_options('status', 'sampling rate', rrate)

    def update_limits(self, limit):
        self.context.update_thread_options('motor', 'high limit', float(self.le_motor_hl.text()))
        self.context.update_thread_options('motor', 'low limit', float(self.le_motor_ll.text()))

    def update_tol(self, tol):
        self.context.update_thread_options('motor', 'step size', tol)

    def update_motor_avg(self, avg):
        self.context.update_thread_options('motor', 'averaging', avg)

    def update_algorithm(self, alg):
        self.context.update_thread_options('motor', 'algorithm', alg)

    def receive_message(self, message):
        self.text_area.append(message)

    def checkBttn(self, button):
        bttn = button.text()
        if bttn == "simulated data":
            self.rdbttn_manual.click()
            self.rdbttn_auto.setEnabled(False)
            self.context.run_live(0)
        elif bttn == "live data":
            self.rdbttn_auto.setEnabled(True)
            self.context.run_live(1)
        elif bttn == "manual motor moving":
            self.bttn_search.setEnabled(False)
            self.bttn_tracking.setEnabled(False)
            self.bttn_stop_motor.setEnabled(False)
        elif bttn == "automated motor moving":
            self.bttn_search.setEnabled(True)
            self.bttn_tracking.setEnabled(True)
            self.bttn_stop_motor.setEnabled(True)
        elif bttn == "calibration in GUI":
            self.context.update_thread_options('status', 'calibration source', bttn)
        elif bttn == "calibration from results":
            self.context.update_thread_options('status', 'calibration source', bttn)

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
