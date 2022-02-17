from PyQt5.QtGui import QPixmap


class JetImageAction(QPixmap):
    def __init__(self, context, signals):
        super(JetImageAction, self).__init__()
        self.context = context
        self.signals = signals
        self.make_connections()

    def make_connections(self):
        self.signals.imageProcessingRequest.connect(self.find_center)

    def find_center(self):
        pass
