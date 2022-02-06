import logging

from gui.widgets.editorWidget import EditorWidget
from gui.widgets.jetImageWidget import JetImageWidget
from PyQt5.QtWidgets import QHBoxLayout, QWidget

log = logging.getLogger('pydm')
log.setLevel('CRITICAL')


class JetImageView(QWidget):
    def __init__(self, context, signals):
        super(JetImageView, self).__init__()
        self.signals = signals
        self.context = context
        self.camera = ""
        self.mainLayout = QHBoxLayout()
        self.createImageWidget()
        self.createEditorWidget()
        self.mainLayout.addWidget(self.imageWidget, 75)
        self.mainLayout.addWidget(self.editorWidget, 25)
        self.setLayout(self.mainLayout)
        self.make_connections()

    def make_connections(self):
        pass

    def createImageWidget(self):
        self.imageWidget = JetImageWidget(self.context, self.signals)

    def createEditorWidget(self):
        self.editorWidget = EditorWidget(self.context, self.signals)
