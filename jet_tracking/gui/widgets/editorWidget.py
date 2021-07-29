from PyQt5.QtWidgets import QFrame
from gui.widgets.editorWidgetUi import Editor_Ui
import collections
import logging

log = logging.getLogger(__name__)


class EditorWidget(QFrame, Editor_Ui):

    def __init__(self, context, signals):
        super(EditorWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)