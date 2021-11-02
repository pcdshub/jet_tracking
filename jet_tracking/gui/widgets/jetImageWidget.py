from PyQt5.QtWidgets import QFrame, QWidget, QGraphicsPixmapItem, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QPixmap
from gui.widgets.jetImageWidgetUi import Image_Ui
from epics import caget
import cv2
import logging
import numpy as np

log = logging.getLogger(__name__)

"""
NTS:
# Create scene
self.image_item = QGraphicsPixmapItem()
scene = QGraphicsScene(self)
scene.addItem(self.image_item)

# Create GraphicView display
self.view = QGraphicsView(scene, self)
# Adding right click menus
self.view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
self.zoomout_action = QAction("Fit canvas", self)
self.view.addAction(self.zoomout_action)

display camera image:
image = QImage(camera_image, w, h, w, QImage.Format_Grayscale8)
self.image_item.setPixmap(QPixmap.fromImage(image))
self.view.fitInView(self.image_item)
"""


class JetImageWidget(QWidget, Image_Ui):

    def __init__(self, context, signals):
        super(JetImageWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.pixmap = QPixmap()
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
