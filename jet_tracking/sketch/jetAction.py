from PyQt5.QtGui import QPixmap


class JetImageAction(QPixmap):
    def __init__(self, context, signals):
        super(JetImageAction, self).__init__()
        self.context = context
        self.signals = signals



