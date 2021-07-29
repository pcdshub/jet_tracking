from PyQt5.QtWidgets import QWidget
from gui.windows.simWindowUi import SimWindow_Ui

class SimWindow(QWidget, SimWindow_Ui):

    def __init__(self, context, signals):
        super(SimWindow, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)