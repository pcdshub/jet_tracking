from PyQt5.QtWidgets import QMainWindow, QHBoxLayout
from gui.windows.simWindowUi import SimWindow_Ui
from gui.views.simultationView import SimulationView


class SimWindow(QMainWindow, SimWindow_Ui):
    def __init__(self, context, signals):
        super(SimWindow, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.create_views_and_dialogs()
        self.setCentralWidget(self.simulationView)

    def create_views_and_dialogs(self):
        self.simulationView = SimulationView(self.context, self.signals, self)

    def closeEvent(self, e):
        self.context.update_live_motor(True)