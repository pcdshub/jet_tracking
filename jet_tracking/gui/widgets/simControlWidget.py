import logging

from gui.widgets.simControlWidgetUi import SimUi
from PyQt5.QtWidgets import QFrame

log = logging.getLogger(__name__)


class SimWidget(QFrame, SimUi):

    def __init__(self, context, signals):
        super().__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.make_connections()
        self.set_sim_options()

    def set_sim_options(self):
        self.context.update_dropped_shots(float(self.box_percent_drop.text()))
        self.context.update_peak_intensity(float(self.box_int.text()))
        self.context.update_jet_radius(float(self.box_jet_radius.text()))
        self.context.update_jet_center(float(self.box_jet_center.text()))
        self.context.update_max_intensity(float(self.box_max_int.text()))
        self.context.update_background(float(self.box_bg.text()))

    def make_connections(self):
        self.box_percent_drop.checkVal.connect(
            self.context.update_dropped_shots)
        self.box_int.checkVal.connect(self.context.update_peak_intensity)
        self.box_jet_radius.checkVal.connect(self.context.update_jet_radius)
        self.box_jet_center.checkVal.connect(self.context.update_jet_center)
        self.box_max_int.checkVal.connect(self.context.update_max_intensity)
        self.box_bg.checkVal.connect(self.context.update_background)
        self.signals.updateRunValues.connect(self.send_values)

    def send_values(self, live):
        # this is important because jet location for running live is determined by crosshairs
        if not live:
            self.context.update_jet_center(float(self.box_jet_center.text()))
