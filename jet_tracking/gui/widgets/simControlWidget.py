from datastream import MotorThread, StatusThread
from gui.widgets.simControlWidgetUi import SimUi
from PyQt5.QtWidgets import QFrame
import logging

log = logging.getLogger(__name__)

class SimWidget(QFrame, SimUi):

    def __init__(self, context, signals):
        super(SimWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.worker_motor = None
        self.worker_status = None
        self.setupUi(self)
        self.make_connections()
        self.set_sim_options()
        self.initialize_threads()

    def initialize_threads(self):
        self.worker_status = StatusThread(self.context, self.signals)
        self.worker_motor = MotorThread(self.context, self.signals)

    def set_sim_options(self):
        self.context.update_motor_position(float(self.box_motor_pos.text()))
        self.context.update_dropped_shots(float(self.box_percent_drop.text()))
        self.context.update_peak_intensity(float(self.box_int.text()))
        self.context.update_jet_radius(float(self.box_jet_radius.text()))
        self.context.update_jet_center(float(self.box_jet_center.text()))
        self.context.update_max_intensity(float(self.box_max_int.text()))
        self.context.update_background(float(self.box_bg.text()))

    def make_connections(self):
        self.box_motor_pos.checkVal.connect(self.context.update_motor_position)
        self.box_percent_drop.checkVal.connect(
            self.context.update_dropped_shots)
        self.box_int.checkVal.connect(self.context.update_peak_intensity)
        self.box_jet_radius.checkVal.connect(self.context.update_jet_radius)
        self.box_jet_center.checkVal.connect(self.context.update_jet_center)
        self.box_max_int.checkVal.connect(self.context.update_max_intensity)
        self.box_bg.checkVal.connect(self.context.update_background)

    def send_values(self, live):
        if not live:
            self.context.update_motor_position(float(self.box_motor_pos.text()))
            self.context.update_jet_center(float(self.box_jet_center.text()))
