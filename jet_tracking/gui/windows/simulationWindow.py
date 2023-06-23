from gui.views.simultationView import SimulationView
from gui.windows.simWindowUi import SimWindow_Ui
from PyQt5.QtWidgets import QMainWindow


class SimWindow(QMainWindow, SimWindow_Ui):
    """
    This class represents the simulation window of the application and inherits from both QMainWindow and SimWindow_Ui classes.
    """
    def __init__(self, context, signals):
        """

        Constructor method for the SimWindow class.

        Parameters
        ----------
        context: the context class
        signals: the signals class

        """
        super().__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.simulationView = None
        self.create_views_and_dialogs()
        self.setCentralWidget(self.simulationView)

    def create_views_and_dialogs(self):
        """Creates an instance of the SimulationView class and assigns it to the simulationView attribute."""
        self.simulationView = SimulationView(self.context, self.signals, self)

    def closeEvent(self, e):
        """Overrides the close event method to perform any necessary actions when the simulation window is closed."""
        super(QMainWindow, self).closeEvent(e)
