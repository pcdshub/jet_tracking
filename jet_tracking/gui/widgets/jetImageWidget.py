import logging
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsView
from tools.ROI import HLineItem, VLineItem, GraphicsScene, GraphicsRectItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
from qimage2ndarray import array2qimage
import cv2

log = logging.getLogger("jet_tracker")


class JetImageWidget(QGraphicsView):

    def __init__(self, context, signals):
        super().__init__()
        log.debug("Supplying Thread information from init of jetImageWidget")
        self.signals = signals
        self.context = context
        self.scene = GraphicsScene()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.qimage = QImage()
        self.image = np.zeros([500, 500, 3], dtype=np.uint8)
        self.color_image = np.zeros([500, 500, 3], dtype=np.uint8)
        self.pixmap_item = QGraphicsPixmapItem()
        self.line_item_hor_top = HLineItem()
        self.line_item_hor_bot = HLineItem()
        self.line_item_vert_left = VLineItem()
        self.line_item_vert_right = VLineItem()
        self.rect = GraphicsRectItem(100, 100, 100, 100)
        self.find_com_bool = False
        self.image_displayed = False
        self.contours = []
        self.best_fit_line = []
        self.best_fit_line_plus = []
        self.best_fit_line_minus = []
        self.com = []
        self.beam_location = ()
        self.make_connections()

    def connect_scene(self):
        self.setScene(self.scene)
        self.scene.addItem(self.pixmap_item)
        self.scene.addItem(self.line_item_vert_right)
        self.scene.addItem(self.line_item_vert_left)
        self.scene.addItem(self.line_item_hor_bot)
        self.scene.addItem(self.line_item_hor_top)
        self.scene.addItem(self.rect)
        
    def make_connections(self):
        self.signals.camImager.connect(self.update_image)
        self.scene.sceneRectChanged.connect(self.capture_scene_change)
        self.signals.comDetection.connect(self.set_com_on)
        self.scene.lineItemPos.connect(self.send_line_pos)
        self.scene.rectItemPos.connect(self.rect_pos)

    def rect_pos(self):
        scene_coord = self.rect.mapToScene(self.rect.boundingRect().center())
        pixmap_coord = self.pixmap_item.mapFromScene(scene_coord)
        self.beam_location = (pixmap_coord.x(), pixmap_coord.y())

    def send_line_pos(self):
        upper_left = (self.line_item_vert_left.pos().x(), 
                      self.line_item_hor_top.pos().y())
        lower_right = (self.line_item_vert_right.pos().x(), 
                       self.line_item_hor_bot.pos().y())
        self.signals.linesInfo.emit(upper_left, lower_right)

    def set_com_on(self):
        self.find_com_bool = self.context.find_com_bool

    def update_image(self, im):
        # need to do something so that at the end of the calibration it also collects
        # multiple images.. also it just needs to be regularly finding the line if you want to
        # try to automate shut offs and such
        self.image = im
        self.image = cv2.convertScaleAbs(self.image)
        self.color_image = cv2.cvtColor(self.image, cv2.COLOR_GRAY2RGB)
        self.color_image = cv2.drawContours(self.color_image,
                                            self.context.contours, -1, (0, 255, 0), 3)
        if self.find_com_bool:
            for point in self.context.com:
                self.color_image = cv2.circle(self.color_image, 
                                              tuple(point), 1, (0, 255, 255))
            if len(self.context.best_fit_line):
                self.color_image = cv2.line(self.color_image, 
                                            tuple(self.context.best_fit_line[1]),
                                            tuple(self.context.best_fit_line[0]), 
                                            (0, 255, 255), 2)
            if len(self.context.best_fit_line_plus):
                self.color_image = cv2.line(self.color_image, 
                                            tuple(self.context.best_fit_line_plus[1]),
                                            tuple(self.context.best_fit_line_plus[0]), 
                                            (220, 20, 60), 1)
            if len(self.context.best_fit_line_minus):
                self.color_image = cv2.line(self.color_image, tuple(self.context.best_fit_line_minus[1]),
                                            tuple(self.context.best_fit_line_minus[0]), 
                                            (220, 20, 60), 1)
        self.qimage = array2qimage(self.color_image)
        pixmap = QPixmap.fromImage(self.qimage) 
        self.pixmap_item.setPixmap(pixmap)
        if not self.image_displayed:
            self.image_displayed = True
            self.connect_scene()
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

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
        self.send_line_pos()

    def resizeEvent(self, event):
        if not self.pixmap_item.pixmap().isNull():
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_hor_top, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_vert_left, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_hor_bot, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_vert_right, Qt.KeepAspectRatio)
        super().resizeEvent(event)
