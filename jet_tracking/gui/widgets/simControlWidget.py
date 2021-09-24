from PyQt5.QtWidgets import QFrame
from gui.widgets.simControlWidgetUi import Sim_Ui
import logging

log = logging.getLogger(__name__)


class SimWidget(QFrame, Sim_Ui):

    def __init__(self, context, signals):
        super(SimWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)