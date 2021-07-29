from PyQt5.QtWidgets import QFrame
from gui.widgets.jetImageWidgetUi import Image_Ui
import collections
import logging

log = logging.getLogger(__name__)


class JetImageWidget(QFrame, Image_Ui):

    def __init__(self, context, signals):
        super(JetImageWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
