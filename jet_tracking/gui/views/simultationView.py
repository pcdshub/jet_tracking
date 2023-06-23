from gui.widgets.simControlWidget import SimWidget
from PyQt5.QtWidgets import QHBoxLayout, QWidget


class SimulationView(QWidget):

    def __init__(self, context, signals, parent=None):
        super().__init__(parent)
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