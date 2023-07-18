import logging

import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QFrame, QMessageBox

from ...datastream import MotorThread, StatusThread
from ..widgets.controlWidgetUi import Controls_Ui

log = logging.getLogger('jet_tracker')


class ControlsWidget(QFrame, Controls_Ui):
    """
    Widget class for controlling and monitoring a motor.

    Inherits from QFrame and uses a separate UI file for setting up the user interface.
    """
    def __init__(self, context, signals):
        """
        Initialize the ControlsWidget.

        Args:
            context: The context object containing various settings and values.
            signals: The signals object for emitting and receiving signals.

        """
        super().__init__()
        log.debug("Supplying Thread information from init of Controls Widget")
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.thread1 = QThread()
        self.thread2 = QThread()
        self.worker_status = StatusThread()
        self.worker_motor = MotorThread()
        self.msg = QMessageBox()
        self.msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.msg.setDefaultButton(QMessageBox.No)
        self.set_thread_options()
        self.set_motor_options()
        self.make_connections()

    def set_thread_options(self):
        """
        Update the UI elements related to thread options based on the values stored in the context.

        """
        self.le_percent.setText(str(self.context.percent))
        self.le_ave_graph.setText(str(self.context.graph_ave_time))
        self.le_refresh_rate.setText(str(self.context.refresh_rate))
        self.le_x_axis.setText(str(self.context.display_time))
        self.le_number_calibration.setText(str(self.context.num_cali))
        self.le_bad_scan.setText(str(self.context.bad_scan_limit))

    def set_motor_options(self):
        """
        Update the UI elements related to motor options based on the values stored in the context.

        """
        self.le_motor_pos.setText(str(self.context.motor_position))
        self.le_motor_ll.setText(str(self.context.low_limit))
        self.le_motor_hl.setText(str(self.context.high_limit))
        self.le_size.setText(str(self.context.step_size))
        self.cbox_algorithm.setCurrentText(self.context.algorithm)

    def make_connections(self):
        """
        Set up the signal-slot connections between UI elements and methods in the class.

        """
        self.signals.terminateAll.connect(self.terminate_all)
        self.le_number_calibration.checkVal.connect(self.context.update_num_cali)
        self.le_percent.checkVal.connect(self.context.update_percent)
        self.le_refresh_rate.checkVal.connect(self.context.update_refresh_rate)
        self.le_ave_graph.checkVal.connect(self.context.update_graph_averaging)
        self.le_bad_scan.checkVal.connect(self.context.update_scan_limit)
        self.le_motor_ll.checkVal.connect(self.update_limits)
        self.le_motor_hl.checkVal.connect(self.update_limits)
        self.le_motor_pos.checkVal.connect(self.move_motor)
        self.le_size.checkVal.connect(self.context.update_step_size)
        self.le_ave_motor.checkVal.connect(self.context.update_motor_averaging)
        self.cbox_algorithm.currentTextChanged.connect(self.context.update_algorithm)
        self.bttngrp1.buttonClicked.connect(self.checkBttn)
        self.bttngrp2.buttonClicked.connect(self.checkBttn)
        self.bttngrp3.buttonClicked.connect(self.checkBttn)
        self.bttngrp4.buttonClicked.connect(self.checkBttn)
        self.signals.showMessageBox.connect(self.show_dialog)
        self.msg.buttonClicked.connect(self.popup_clicked)

        self.bttn_connect_motor.clicked.connect(self.context.connect_motor)
        self.bttn_search.clicked.connect(self.start_algorithm)
        self.bttn_stop_current_scan.clicked.connect(self._stop_scanning)
        self.bttn_tracking.clicked.connect(self._enable_tracking)
        self.bttn_stop_motor.clicked.connect(self._stop_motor)
        self.signals.trackingStatus.connect(self.set_tracking_status)

        self.signals.changeStatus.connect(self.set_monitor_status)
        self.signals.changeCalibrationDisplay.connect(self.set_calibration)
        self.signals.plotMotorMoves.connect(self.plot_motor_moves)
        self.signals.changeReadPosition.connect(self.update_read_motor)
        self.signals.changeMotorPosition.connect(self.update_motor_position)
        self.signals.message.connect(self.receive_message)

        self.bttn_stop.clicked.connect(self._stop)
        self.bttn_calibrate.clicked.connect(self._calibrate)
        self.bttn_start.clicked.connect(self.start_processes)

        self.worker_status.moveToThread(self.thread1)
        self.worker_motor.moveToThread(self.thread2)
        self.worker_status.init_after_move(self.context, self.signals)
        self.worker_motor.init_after_move(self.context, self.signals)

        self.thread1.started.connect(self.worker_status.start_com)
        self.thread2.started.connect(self.worker_motor.start_com)
        self.thread1.start()
        self.thread2.start()
        self.le_x_axis.checkVal.connect(self.context.update_display_time)

    def start_processes(self):
        """
        Start the motor connection and the status thread when the "Start" button is clicked.

        """
        self.worker_motor.connect_to_motor()
        self.worker_status.reader.initialize_connections()
        if self.worker_status.reader.connected:
            self.signals.startStatusThread.emit()
            if self.worker_motor.connected:
                self._start_motor()
            else:
                self.signals.message.emit("Motor is not connected.\n"
                                          "Fix motor connection settings"
                                          " and try again")
        else:
            self.signals.message.emit("The Value reader is not connecting"
                                      " properly. Check settings/PVs.")

    def start_algorithm(self):
        """
        Update the motor mode to "run" when the "Search" button is clicked.

        """
        self.context.update_motor_mode("run")

    def _stop(self):
        """
        Handle the stop button click event.

        """
        if not self.worker_status.paused:
            self.signals.stopStatusThread.emit(False)
        if not self.worker_motor.paused:
            self.signals.stopMotorThread.emit(False)

    def _calibrate(self):
        """
        Handle the calibrate button click event.

        """
        if self.worker_status.paused:
            self.text_area.append("You are not running so there's \
                  nothing to calibrate.. hit start first")
        else:
            self.context.set_mode("calibrate")

    def _enable_tracking(self):
        """
        Handle the enable tracking button click event.

        """
        self.set_tracking_status("enabled", "green")
        self.signals.enableTracking.emit(True)

    def _start_motor(self):
        """
        Start the motor when the conditions are met.

        """
        if not self.thread2.isRunning():
            if self.thread1.isRunning():
                self.context.update_motor_mode('sleep')
                self.signals.startMotorThread.emit()
            else:
                self.signals.message.emit("You must start getting points "
                                          "first!")
        else:
            if not self.worker_motor.paused:
                self.signals.startMotorThread.emit()

    def _stop_motor(self):
        """
        Stop the motor when the conditions are met.

        """
        if not self.worker_motor.paused:
            self.signals.stopMotorThread.emit(False)
            self.signals.message.emit("The motor was stopped"
                                      "either press start or connect motor")
            # self.context.update_tracking(False)
            self.set_tracking_status('disabled', "red")
        else:
            self.signals.message.emit("The motor is not running")

    def _stop_scanning(self):
        """
        Stop the scanning process when the conditions are met.

        """
        if self.thread2.isRunning():
            self.signals.endEarly.emit()
        else:
            self.signals.message.emit("You aren't scanning!")

    def move_motor(self, mp):
        """
        Move the motor to the specified position.

        Args:
            mp: The position to move the motor to.

        """
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

    def plot_motor_moves(self, position, maximum, positions, intensities, save=False):
        """
        Plot the motor positions and intensities.

        Args:
            position: The position for maximum intensity.
            maximum: The maximum intensity value.
            positions: The motor positions.
            intensities: The intensities corresponding to the motor positions.
            save: Whether to save the plot and data.

        """
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
        """
        Update the motor position display.

        Args:
            p: The new motor position.

        """
        self.le_motor_pos.setText(str(p))

    def update_read_motor(self, mp):
        """
        Update the read motor display.

        Args:
            mp: The motor position.

        """
        self.lbl_motor_status.display(mp)

    def clearLayout(self, layout):
        """
        Remove all widgets from the given layout.

        Args:
            layout: The layout to clear.

        """
        for i in reversed(range(layout.count())):
            widgetToRemove = layout.itemAt(i).widget()
            layout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

    def set_tracking_status(self, status, color):
        """
        Set the tracking status label and style.

        Args:
            status: The tracking status.
            color: The background color of the label.

        """
        self.lbl_tracking_status.setText(status)
        self.lbl_tracking_status.setStyleSheet(f"\
                background-color: {color};")

    def set_monitor_status(self, status, color):
        """
        Set the monitor status label and style.

        Args:
            status: The monitor status.
            color: The background color of the label.

        """
        self.lbl_monitor_status.setText(status)
        self.lbl_monitor_status.setStyleSheet(f"\
                background-color: {color};")

    def update_limits(self, limit):
        """
        Update the motor limit display.

        Args:
            limit: The new motor limit value.

        """
        self.context.update_limits(float(self.le_motor_hl.text()),
                                   float(self.le_motor_ll.text()))

    def receive_message(self, message):
        """
        Receive and display a message in the text area.

        Args:
            message (str): The message to be displayed.
        """
        pt = self.text_area.toPlainText()
        if pt.split('\n')[-1] == message.split('\n')[-1]:
            pass
        else:
            self.text_area.append(message)

    def show_dialog(self, go_from, go_to):
        """
        Show a dialog box to confirm data viewing changes.

        Args:
            go_from (str): The current data viewing option.
            go_to (str): The new data viewing option.
        """
        self.msg.setWindowTitle("Data Viewing Changes")
        self.msg.setText(
            f"Would you like to change the \n"
            f"data from {go_from} to {go_to}?"
        )
        self.msg.show()

    def popup_clicked(self, i):
        """
        Handle the click event on the popup message box.

        Args:
            i: The clicked item.
        """
        if i.text() == "&Yes":
            self._stop()
            self.signals.message.emit("Must press start to run in this new mode")
            if self.bttngrp1.checkedId() == 1:  # live
                self.context.update_live_graphing(True)
                self.context.update_live_motor(True)
            if self.bttngrp1.checkedId() == 0:  # simulated
                self.context.update_live_graphing(False)
                self.context.update_live_motor(False)
        else:
            if self.bttngrp1.checkedId() == 1:
                self.rdbttn_all_sim.setChecked(True)
            elif self.bttngrp1.checkedId() == 0:
                self.rdbttn_live.setChecked(True)

    def checkBttn(self, button):
        """
        Handle the button click event to change settings.

        Args:
            button: The clicked button.
        """
        bttn = button.text()
        if bttn == "All simulated":
            if not self.worker_motor.paused:
                print("Motor running and trying to change to simulated")
                self.signals.showMessageBox.emit("live", "simulated")
            else:
                self.context.update_live_graphing(False)
                self.context.update_live_motor(False)
        elif bttn == "Live data":
            if not self.worker_motor.paused:
                self.signals.showMessageBox.emit("simulated", "live")
            else:
                self.context.update_live_graphing(True)
                self.context.update_live_motor(True)
        elif bttn == "Sim data + Live motor/image":
            self.context.update_live_graphing(False)
            self.context.update_live_motor(True)
        elif bttn == "manual \nmotor moving":
            self.bttn_search.setEnabled(True)
            self.bttn_tracking.setEnabled(False)
        elif bttn == "automated \nmotor moving":
            self.bttn_search.setEnabled(True)
            self.bttn_tracking.setEnabled(True)
        elif bttn == "calibration in GUI":
            self.context.update_calibration_source(bttn)
        elif bttn == "calibration from results":
            self.context.update_calibration_source(bttn)
        elif bttn == "calibrate after completed":
            self.context.update_calibration_priority("recalibrate")
        elif bttn == "keep current calibration":
            self.context.update_calibration_priority("keep calibration")

    def setDefaultStyleSheet(self):
        """
        Set the default style sheet for the widget.
        """
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

    def terminate_all(self):
        """
        Terminate all running threads and perform cleanup tasks.
        """
        self.signals.stopStatusThread.emit(True)
        self.signals.stopMotorThread.emit(True)
        self.thread1.quit()
        self.thread1.wait()
        self.thread2.quit()
        self.thread2.wait()
