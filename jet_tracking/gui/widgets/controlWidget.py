import logging

import matplotlib.pyplot as plt
import numpy as np
from datastream import MotorThread, StatusThread
from gui.widgets.controlWidgetUi import Controls_Ui
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QFrame, QMessageBox

log = logging.getLogger(__name__)


class ControlsWidget(QFrame, Controls_Ui):

    def __init__(self, context, signals):
        super(ControlsWidget, self).__init__()
        log.info("Main Thread: %d" % QThread.currentThreadId())
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.worker_status = None
        self.worker_motor = None
        self.msg = QMessageBox()
        self.msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.msg.setDefaultButton(QMessageBox.No)
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
        self.le_number_calibration.setText(str(self.context.num_cali))
        self.le_bad_scan.setText(str(self.context.bad_scan_limit))

    def set_motor_options(self):
        self.le_motor_pos.setText(str(self.context.motor_position))
        self.le_motor_ll.setText(str(self.context.low_limit))
        self.le_motor_hl.setText(str(self.context.high_limit))
        self.le_size.setText(str(self.context.step_size))
        self.cbox_algorithm.setCurrentText(self.context.algorithm)

    def make_connections(self):
        self.le_number_calibration.checkVal.connect(self.context.update_num_cali)
        self.le_percent.checkVal.connect(self.context.update_percent)
        self.le_refresh_rate.checkVal.connect(self.context.update_refresh_rate)
        self.le_ave_graph.checkVal.connect(self.context.update_graph_averaging)
        self.le_bad_scan.checkVal.connect(self.context.update_scan_limit)
        self.le_motor_ll.checkVal.connect(self.update_limits)
        self.le_motor_hl.checkVal.connect(self.update_limits)
        self.le_motor_pos.checkVal.connect(self.move_motor)
        self.le_x_axis.checkVal.connect(self.context.update_display_time)
        self.le_size.checkVal.connect(self.context.update_step_size)
        self.le_ave_motor.checkVal.connect(self.context.update_motor_averaging)
        self.cbox_algorithm.currentTextChanged.connect(
            self.context.update_algorithm)
        self.bttngrp1.buttonClicked.connect(self.checkBttn)
        self.bttngrp2.buttonClicked.connect(self.checkBttn)
        self.bttngrp3.buttonClicked.connect(self.checkBttn)
        self.signals.showMessageBox.connect(self.show_dialog)
        self.msg.buttonClicked.connect(self.popup_clicked)

        self.bttn_connect_motor.clicked.connect(self.context.connect_motor)
        self.bttn_search.clicked.connect(self.start_algorithm)
        self.bttn_stop_current_scan.clicked.connect(self._stop_scanning)
        self.bttn_tracking.clicked.connect(self._enable_tracking)
        self.bttn_stop_motor.clicked.connect(self._stop_motor)
        self.signals.trackingStatus.connect(self.set_tracking_status)

        self.bttn_stop.clicked.connect(self._stop)
        self.bttn_calibrate.clicked.connect(self._calibrate)
        self.bttn_start.clicked.connect(self.start_processes)

        self.signals.changeStatus.connect(self.set_monitor_status)
        self.signals.changeCalibrationDisplay.connect(self.set_calibration)
        self.signals.plotMotorMoves.connect(self.plot_motor_moves)
        self.signals.changeReadPosition.connect(self.update_read_motor)
        self.signals.changeMotorPosition.connect(self.update_motor_position)
        self.signals.message.connect(self.receive_message)
        self.signals.updateRunValues.connect(self.send_values)

    def start_processes(self):
        self.worker_motor.connect_to_motor()
        self.worker_status.reader.initialize_connections()
        if self.worker_status.reader.connected:
            self.worker_status.start()
            if self.worker_motor.connected:
                self._start_motor()
            else:
                self.signals.message.emit("Motor is not connected.\n"
                                          "fix motor connection settings"
                                          "and try again")
        else:
            self.signals.message.emit("The Value reader is not connecting"
                                      "properly. Check settings.")

    def start_algorithm(self):
        self.context.update_motor_mode("run")

    def _stop(self):
        if self.worker_status.isRunning():
            self.worker_status.requestInterruption()
            self.worker_status.wait()
        if self.worker_motor.isRunning():
            self._stop_motor()
            #self.worker_motor.requestInterruption()
            #self.worker_motor.wait()

    def _calibrate(self):
        if not self.worker_status.isRunning():
            self.text_area.append("You are not running so there's \
                  nothing to calibrate.. hit start first")
        else:
            self.context.set_mode("calibrate")

    def _enable_tracking(self):
        self.set_tracking_status("enabled", "green")
        self.context.update_tracking(True)

    def _start_motor(self):
        if not self.worker_motor.isRunning():
            if self.worker_status.isRunning():
                self.context.update_motor_running(False)
                self.context.update_motor_mode('sleep')
                self.worker_motor.start()
            else:
                self.signals.message.emit("You must start getting points "
                                          "first!")
        else:
            if not self.worker_motor.isInterruptionRequested():
                self.worker_motor.start()
            else:
                self.signals.message.emit("The motor thread is already started")

    def _stop_motor(self):
        if self.worker_motor.isRunning():
            self.context.update_motor_running(False)
            print(self.worker_motor.isRunning())
            self.worker_motor.requestInterruption()
            print(self.worker_motor.isRunning())
            self.worker_motor.quit()
            print(self.worker_motor.isRunning())
            self.signals.message.emit("The motor was stopped"
                                      "either press start or connect motor")
            self.context.update_tracking(False)
            self.set_tracking_status('disabled', "red")
        else:
            self.signals.message.emit("The motor is not running")

    def _stop_scanning(self):
        if self.worker_motor.isRunning():
            self.signals.endEarly.emit()
        else:
            self.signals.message.emit("You aren't scanning!")

    def move_motor(self, mp):
        if mp > self.context.high_limit or mp < self.context.low_limit:
            self.le_motor_pos.setText(str(self.context.motor_position))
            self.signals.message.emit("You tried to input a motor position \n"
                                      "outside of the range set by the limits."
                                      " Either set new limits or try a different\n"
                                      " value.")
        elif self.worker_motor.connected:
            self.worker_motor.move_to_input_position(mp)
        else:
            self.le_motor_pos.setText(str(self.context.motor_position))
            self.signals.message.emit("The motor is not connected \n"
                                      "so the position cannot be changed")

    def plot_motor_moves(self, position, maximum, positions, intensities,
                         save=False):
        plt.figure()
        plt.xlabel('motor position')
        plt.ylabel('I/I0 intensity')
        plt.plot(position, maximum, 'ro')
        x = positions
        y = intensities
        plt.scatter(x, y)
        plt.show()
        if save:
            folder = self.context.SAVEFOLDER.format(self.context.HUTCH,
                                                    self.context.EXPERIMENT)
            plotfile = folder+'/motor_figure_%s.png'
            datafile = folder+'/motor_data_%s.csv'
            try:
                plt.savefig(plotfile)
                np.savetxt(datafile, *[positions, intensities])
            except Exception as e:
                log.warning("Saving files failed!\n%s", e)

    def set_calibration(self):
        """Updates the display when a successful calibration is complete."""
        self.lbl_i0_status.display(
            self.context.calibration_values['i0']['mean'])
        self.lbl_diff_status.display(
            self.context.calibration_values['diff']['mean'])

    def update_motor_position(self, p):
        self.le_motor_pos.setText(str(p))

    def update_read_motor(self, mp):
        self.lbl_motor_status.display(mp)

    def send_values(self, live):
        if live:
            self.context.update_limits(float(self.le_motor_hl.text()),
                                       float(self.le_motor_ll.text()))
            self.context.step_size = self.le_size.text()
            self.context.motor_averaging = self.le_ave_motor.text()
            self.context.connect_motor()

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

    def update_limits(self, limit):
        self.context.update_limits(float(self.le_motor_hl.text()),
                                   float(self.le_motor_ll.text()))

    def receive_message(self, message):
        pt = self.text_area.toPlainText()
        if pt.split('\n')[-1] == message.split('\n')[-1]:
            pass
        else:
            self.text_area.append(message)

    def show_dialog(self, go_from, go_to):
        self.msg.setWindowTitle("Data Viewing Changes")
        self.msg.setText(f"Would you like to change the \n"
                    f"data from {go_from} to {go_to}?")
        self.msg.show()

    def popup_clicked(self, i):
        if i.text() == "&Yes":
            self._stop()
            self.signals.message.emit("Must press start to run in this new mode")
            if self.bttngrp1.checkedId() == 1: # live
                self.context.update_live_graphing(True)
                self.context.update_live_motor(True)
            if self.bttngrp1.checkedId() == 0: # simulated
                self.context.update_live_graphing(False)
                self.context.update_live_motor(False)
        else:
            print("here")
            if self.bttngrp1.checkedId() == 1:
                self.rdbttn_sim.setChecked(True)
            elif self.bttngrp1.checkedId() == 0:
                self.rdbttn_live.setChecked(True)

    def checkBttn(self, button):
        bttn = button.text()
        if bttn == "simulated data":
            if self.worker_status.isRunning():
                print("worker running and trying to change to simulated")
                self.signals.showMessageBox.emit("live", "simulated")
            else:
                self.context.update_live_graphing(False)
                self.context.update_live_motor(False)
        elif bttn == "live data":
            print("worker running and trying to change to live")
            if self.worker_status.isRunning():
                self.signals.showMessageBox.emit("simulated", "live")
            else:
                self.context.update_live_graphing(True)
                self.context.update_live_motor(True)
        elif bttn == "manual \nmotor moving":
            self.bttn_search.setEnabled(True)
            self.bttn_tracking.setEnabled(False)
            self.context.update_manual_motor(True)
        elif bttn == "automated \nmotor moving":
            self.bttn_search.setEnabled(True)
            self.bttn_tracking.setEnabled(True)
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
