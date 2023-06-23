import logging

from gui.widgets.controlWidget import ControlsWidget
from gui.widgets.graphWidget import GraphsWidget
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QDockWidget, QHBoxLayout, QSizePolicy, QWidget

pydm_log = logging.getLogger('pydm')
pydm_log.setLevel('CRITICAL')


class JetTrackerView(QWidget):
    """This class represents the view widget for the jet tracking functionality within the main window."""
    def __init__(self, context, signals, parent=None):
        """

        Constructor method for the JetTrackerView class.

        Parameters
        ----------
        context: the context object
        signals: the signals object
        parent: option parent widget

        The __init__ method performs the following actions:
        Calls the parent class constructor.
        Initializes the signals, context, and parent attributes.
        Initializes the graphWidget, controlsDock, controlsWidget, and mainLayout attributes.
        Calls the create_graph_widget method to create and assign the GraphsWidget instance to the graphWidget attribute.
        Calls the create_dock_widgets method to create and assign the QDockWidget instance to the controlsDock attribute, and the ControlsWidget instance to the controlsWidget attribute.
        Adds the controlsDock and graphWidget to the mainLayout.
        Sets the layout of the widget using the setLayout method.
        """
        super().__init__(parent)
        self.signals = signals
        self.context = context
        self.parent = parent
        self.graphWidget = None
        self.controlsDock = None
        self.controlsWidget = None
        self.mainLayout = QHBoxLayout()
        self.create_graph_widget()
        self.create_dock_widgets()
        self.mainLayout.addWidget(self.controlsDock, 30)
        self.mainLayout.addWidget(self.graphWidget, 70)
        self.setLayout(self.mainLayout)

    def create_graph_widget(self):
        """Creates an instance of the GraphsWidget class and assigns it to the graphWidget attribute.
        The GraphsWidget represents the graphical visualization of the jet tracking data."""
        self.graphWidget = GraphsWidget(context=self.context,
                                        signals=self.signals)
        self.graphWidget.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Preferred)

    def create_dock_widgets(self):
        """Creates an instance of the QDockWidget class and assigns it to the controlsDock attribute.
        The QDockWidget provides a dockable container for the ControlsWidget, which represents the user
        interface controls related to the jet tracking functionality."""
        self.parent.setDockNestingEnabled(True)
        self.controlsDock = QDockWidget("Controls", self)
        self.controlsDock.setAllowedAreas(Qt.RightDockWidgetArea
                                          | Qt.BottomDockWidgetArea)
        self.controlsDock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.controlsWidget = ControlsWidget(self.context, self.signals)
        self.controlsDock.setWidget(self.controlsWidget)
        self.controlsDock.setSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Preferred)