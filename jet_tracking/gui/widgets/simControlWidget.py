from datastream import MotorThread, StatusThread
from gui.widgets.simControlWidgetUi import Sim_Ui
from PyQt5.QtWidgets import QFrame


class SimWidget(QFrame, Sim_Ui):

    def __init__(self, context, signals):
        super(SimWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.make_connections()
        self.set_sim_options()
        self.initialize_threads()

    def initialize_threads(self):
        self.worker_status = StatusThread(self.context, self.signals)
        self.worker_motor = MotorThread(self.context, self.signals)

    def set_sim_options(self):
        # self.context.update_motor_position(float(self.box_motor_pos.text()))
        self.context.update_dropped_shots(float(self.box_percent_drop.text()))
        self.context.update_peak_intensity(float(self.box_int.text()))
        self.context.update_jet_radius(float(self.box_jet_radius.text()))
        self.context.update_jet_center(float(self.box_jet_center.text()))
        self.context.update_max_intensity(float(self.box_max_int.text()))
        self.context.update_background(float(self.box_bg.text()))
        self.box_motor_pos.setText(str(self.context.motor_position))
        # self.context.update_algorithm(self.cbox_algorithm.currentText())

    def make_connections(self):
        # self.box_motor_pos.checkVal.connect(self.context.update_motor_position)
        self.box_percent_drop.checkVal.connect(
            self.context.update_dropped_shots)
        self.box_int.checkVal.connect(self.context.update_peak_intensity)
        self.box_jet_radius.checkVal.connect(self.context.update_jet_radius)
        self.box_jet_center.checkVal.connect(self.context.update_jet_center)
        self.box_max_int.checkVal.connect(self.context.update_max_intensity)
        self.box_bg.checkVal.connect(self.context.update_background)
        self.bttn_start_tracking.clicked.connect(self.start_tracking)
        self.bttn_stop_tracking.clicked.connect(self.stop_tracking)

    def start_tracking(self):
        self.context.update_tracking(True)
        self.signals.trackingStatus.emit("Sim Tracking", "green")

    def stop_tracking(self):
        self.context.update_tracking(False)
        self.signals.trackingStatus.emit("Not Tracking", "red")

    #     self.cbox_algorithm.currentTextChanged.connect(
    #         self.context.update_algorithm)
    #     self.bttn_start_tracking.clicked.connect(self._start_sim)
    #
    # def _start_sim(self):
    #     self.sim_status.start()
    #
    # def _enable_tracking(self):
    #     self.update_tracking_status("enabled", "green")
    #     self.context.update_tracking(True)
    #     self._start_motor()
    #
    # def set_tracking_status(self, status, color):
    #     self.lbl_tracking_status.setText(status)
    #     self.lbl_tracking_status.setStyleSheet(f"background-color: {color};")
