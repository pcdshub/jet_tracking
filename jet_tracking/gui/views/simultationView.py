from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QSizePolicy, QHBoxLayout, QMainWindow
from gui.widgets.simControlWidget import SimWidget
from signals import Signals
import logging

log = logging.getLogger(__name__)


class SimulationView(QWidget):

    def __init__(self, context, signals, parent=None):
        super(SimulationView, self).__init__(parent)
        self.signals = signals
        self.context = context
        self.parent = parent
        self.mainLayout = QHBoxLayout()
        self.simControlWidget = None
        self.create_editor_widget()
        self.mainLayout.addWidget(self.simControlWidget)
        self.setLayout(self.mainLayout)

    def create_editor_widget(self):
        self.simControlWidget = SimWidget(self.context, self.signals)
