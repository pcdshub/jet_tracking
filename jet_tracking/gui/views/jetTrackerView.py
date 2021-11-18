from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QSizePolicy, QHBoxLayout, QMainWindow

from gui.widgets.controlWidget import ControlsWidget
from gui.widgets.graphWidget import GraphsWidget
import logging

log = logging.getLogger('pydm')
log.setLevel('CRITICAL')


class JetTrackerView(QWidget):

    def __init__(self, context, signals, parent=None):
        super(JetTrackerView, self).__init__(parent)
        self.signals = signals
        self.context = context
        self.parent = parent
        self.mainLayout = QHBoxLayout()
        self.createGraphWidget()
        self.createDockWidgets()
        self.mainLayout.addWidget(self.graphWidget)
        self.mainLayout.addWidget(self.controlsDock)
        self.parent.resizeDocks([self.controlsDock], [45], Qt.Horizontal)
        self.setLayout(self.mainLayout)

    def createGraphWidget(self):
        self.graphWidget = GraphsWidget(context=self.context, signals=self.signals)

    def createDockWidgets(self):
        # maybe the dock needs to be in a frame?? still not able to pop it back in.
        #self.parent.setDockNestingEnabled(True)
        self.controlsDock = QDockWidget("Controls", self)
        self.controlsDock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.controlsDock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.controlsWidget = ControlsWidget(self.context, self.signals)
        self.controlsDock.setWidget(self.controlsWidget)
        self.controlsDock.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)

