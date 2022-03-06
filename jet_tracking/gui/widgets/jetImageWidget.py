import logging
from gui.widgets.jetImageWidgetUi import Image_Ui
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsPixmapItem, QWidget
from sketch.jetAction import JetImageAction

log = logging.getLogger(__name__)


class JetImageWidget(QWidget, Image_Ui):

    def __init__(self, context, signals):
        super(JetImageWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.pixmap = JetImageAction(self.context, self.signals)
        self.pixmap_item = QGraphicsPixmapItem()
        self.make_connections()
        self.setupUi(self)
        self.connect_scene()

    def connect_scene(self):
        self.view.setScene(self.scene)
        self.scene.addItem(self.pixmap_item)

    def make_connections(self):
        self.signals.camImage.connect(self.update_image)

    def update_image(self, im):
        self.pixmap_item.setPixmap(QPixmap.fromImage(im))
