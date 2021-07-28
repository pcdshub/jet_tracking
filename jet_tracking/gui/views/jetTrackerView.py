from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QSizePolicy, QHBoxLayout, QMainWindow

from gui.widgets.controlWidget import ControlsWidget
from gui.widgets.graphWidget import GraphsWidget
from signals import Signals
import logging

log = logging.getLogger('pydm')
log.setLevel('CRITICAL')

class JetTrackerView(QWidget):

    def __init__(self, context, signals):
        super(JetTrackerView, self).__init__()
        self.signals = signals
        self.context = context
        self.mainLayout = QHBoxLayout()
        self.createGraphWidget()
        self.createDockWidgets()
        self.mainLayout.addWidget(self.graphWidget)
        self.mainLayout.addWidget(self.controlsDock)
        self.setLayout(self.mainLayout)

    def createGraphWidget(self):
        self.graphWidget = GraphsWidget(context=self.context, signals=self.signals)

    def createDockWidgets(self):
        #self.setDockNestingEnabled(True)
        self.controlsDock = QDockWidget("Controls", self)
        self.controlsDock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.controlsDock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.controlsWidget = ControlsWidget(self.context, self.signals)
        self.controlsDock.setWidget(self.controlsWidget)
        self.controlsDock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        #self.resizeDocks([self.controlsDock], [45], Qt.Horizontal)
