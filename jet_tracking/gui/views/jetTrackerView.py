import logging

from gui.widgets.controlWidget import ControlsWidget
from gui.widgets.graphWidget import GraphsWidget
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QDockWidget, QHBoxLayout, QSizePolicy, QWidget

pydm_log = logging.getLogger('pydm')
pydm_log.setLevel('CRITICAL')


class JetTrackerView(QWidget):

    def __init__(self, context, signals, parent=None):
        super(JetTrackerView, self).__init__(parent)
        self.signals = signals
        self.context = context
        self.parent = parent
        self.graphWidget = None
        self.controlsDock= None
        self.controlsWidget = None
        self.mainLayout = QHBoxLayout()
        self.create_graph_widget()
        self.create_dock_widgets()
        self.mainLayout.addWidget(self.controlsDock)
        self.mainLayout.addWidget(self.graphWidget)
#        self.parent.resizeDocks([self.controlsDock], [45], Qt.Horizontal)
        self.setLayout(self.mainLayout)

    def create_graph_widget(self):
        self.graphWidget = GraphsWidget(context=self.context,
                                        signals=self.signals)
        self.graphWidget.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Preferred)

    def create_dock_widgets(self):
        # maybe the dock needs to be in a frame?? still not able to pop it back in.
        # self.parent.setDockNestingEnabled(True)
        self.controlsDock = QDockWidget("Controls", self)
        self.controlsDock.setAllowedAreas(Qt.RightDockWidgetArea
                                          | Qt.BottomDockWidgetArea)
        self.controlsDock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.controlsWidget = ControlsWidget(self.context, self.signals)
        self.controlsDock.setWidget(self.controlsWidget)
        self.controlsDock.setSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Preferred)
        # self.mainLayout.addWidget(self.controlsDock)