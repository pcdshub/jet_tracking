import logging

from PyQt5.QtWidgets import QHBoxLayout, QWidget

from ..widgets.editorWidget import EditorWidget
from ..widgets.jetImageWidget import JetImageWidget

log = logging.getLogger('pydm')
log.setLevel('CRITICAL')


class JetImageView(QWidget):
    def __init__(self, context, signals):
        super().__init__()
        self.signals = signals
        self.context = context
        self.camera = ""
        self.mainLayout = QHBoxLayout()
        self.imageWidget = None
        self.editorWidget = None
        self.create_image_widget()
        self.create_editor_widget()
        self.mainLayout.addWidget(self.imageWidget, 75)
        self.mainLayout.addWidget(self.editorWidget, 25)
        self.setLayout(self.mainLayout)
        self.make_connections()

    def make_connections(self):
        pass

    def create_image_widget(self):
        self.imageWidget = JetImageWidget(self.context, self.signals)

    def create_editor_widget(self):
        self.editorWidget = EditorWidget(self.context, self.signals)
