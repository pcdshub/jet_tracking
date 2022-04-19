import logging
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView
from tools.ROI import HLineItem, VLineItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import numpy as np

log = logging.getLogger(__name__)


class JetImageWidget(QGraphicsView):

    def __init__(self, context, signals):
        super(JetImageWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.scene = QGraphicsScene()
        self.image = np.zeros([500,500,3],dtype=np.uint8)
        self.pixmap_item = QGraphicsPixmapItem()
        self.line_item_hor_top = HLineItem()
        self.line_item_hor_bot = HLineItem()
        self.line_item_vert_left = VLineItem()
        self.line_item_vert_right = VLineItem()
        self.make_connections()
        self.connect_scene()

    def connect_scene(self):
        self.setScene(self.scene)
        self.scene.addItem(self.pixmap_item)
        self.scene.addItem(self.line_item_vert_right)
        self.scene.addItem(self.line_item_vert_left)
        self.scene.addItem(self.line_item_hor_bot)
        self.scene.addItem(self.line_item_hor_top)

    def make_connections(self):
        self.signals.camImager.connect(self.update_image)
        self.scene.sceneRectChanged.connect(self.capture_scene_change)
        self.signals.imageProcessingRequest.connect(self.find_center)

    def find_center(self, mp):
        upper_left = (self.line_item_vert_left.scenePos().x(),
                      self.line_item_hor_top.scenePos().y())
        upper_right = (self.line_item_vert_right.scenePos().x(),
                       self.line_item_hor_top.scenePos().y())
        lower_left = (self.line_item_vert_left.scenePos().x(),
                      self.line_item_hor_bot.scenePos().y())
        lower_right = (self.line_item_vert_right.scenePos().x(),
                       self.line_item_hor_bot.scenePos().y())
        center = self.locate_jet(upper_left, upper_right, lower_left,
                                        lower_right)

    def locate_jet(self, ul, ur, ll, lr):

        return

    def update_image(self, im):
        self.image = im
        self.pixmap_item.setPixmap(QPixmap.fromImage(self.image))

    def capture_scene_change(self, qrect):
        self.scene.setSceneRect(qrect)
        self.line_item_hor_top.setLine(0, 0, self.scene.sceneRect().width(), 0)
        self.line_item_hor_top.setPos(0, 0)
        self.line_item_hor_bot.setLine(0, 0, self.scene.sceneRect().width(), 0)
        self.line_item_hor_bot.setPos(0, self.scene.sceneRect().height())
        self.line_item_vert_left.setLine(0, 0, 0, self.scene.sceneRect().height())
        self.line_item_vert_left.setPos(0, 0)
        self.line_item_vert_right.setLine(0, 0, 0, self.scene.sceneRect().height())
        self.line_item_vert_right.setPos(self.scene.sceneRect().width(), 0)

    def resizeEvent(self, event):
        if not self.pixmap_item.pixmap().isNull():
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_hor_top, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_vert_left, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_hor_bot, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_vert_right, Qt.KeepAspectRatio)
        super(JetImageWidget, self).resizeEvent(event)
