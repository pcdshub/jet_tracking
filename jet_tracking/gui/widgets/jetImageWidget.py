from PyQt5.QtWidgets import QFrame, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QImage
from gui.widgets.jetImageWidgetUi import Image_Ui
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


class JetImageWidget(QFrame, Image_Ui):

    def __init__(self, context, signals):
        super(JetImageWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.pixmap = None
        self.ogimage = None
        self.ogimageGray = None
        self.make_connections()
        self.setupUi(self)

    def make_connections(self):
        self.signals.camName.connect(self.display_image)
        self.signals.updateImage.connect(self.update_image)

    def display_image(self, im):
        """
        used to connect to the Camera PV and display it in the
        graphic window
        """
        if im == "":
            self.image = np.zeros((100, 100))
            for i in range(100):
                for j in range(100):
                    self.image[i][j] = 0
                self.image[i][48] = 255
                self.image[i][49] = 255
                self.image[i][50] = 255
        else:
            self.ogimage = cv2.imread(im)
            self.editImage = self.ogimage
            self.ogimageGray = cv2.cvtColor(self.ogimage, cv2.COLOR_BGR2GRAY)
            self.editImageGray = self.ogimageGray

        height, width, channel = self.ogimage.shape
        bytesPerLine = 3*width
        self.qimage = QImage(self.ogimage, width, height, bytesPerLine, QImage.Format_RGB888)
        self.pixmap = QGraphicsPixmapItem(QPixmap(self.qimage))
        self.scene.addItem(self.pixmap)
        self.context.set_images(self.editImage, self.editImageGray)

    def update_image(self, im):

        self.editImageGray = im
        #self.qimage = qi.array2qimage(self.editImageGray, normalize=False)
        self.pixmap = QPixmap(self.qimage)
        self.view.scene().clear()
        self.pixmapItem = QGraphicsPixmapItem()
        self.view.scene().addItem(self.pixmapItem)
        self.pixmapItem.setPixmap(self.pixmap)
