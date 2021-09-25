from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QSizePolicy, QHBoxLayout, QMainWindow

from gui.widgets.sim_editorWidget import SimEditorWidget
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
        self.createEditorWidget()
        self.mainLayout.addWidget(self.editorWidget)
        self.setLayout(self.mainLayout)

    def createEditorWidget(self):
        self.editorWidget = SimEditorWidget(self.context, self.signals)
