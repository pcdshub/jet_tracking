import logging
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView
from tools.ROI import HLineItem, VLineItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
from qimage2ndarray import array2qimage
import cv2
from scipy import stats
import time
import matplotlib.pyplot as plt 

log = logging.getLogger("jet_tracker")


class JetImageWidget(QGraphicsView):

    def __init__(self, context, signals):
        super(JetImageWidget, self).__init__()
        log.debug("Supplying Thread information from init of jetImageWidget")
        self.signals = signals
        self.context = context
        self.scene = QGraphicsScene()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.qimage = QImage()
        self.image = np.zeros([500,500,3], dtype=np.uint8)
        self.color_image = np.zeros([500, 500, 3], dtype=np.uint8)
        self.pixmap_item = QGraphicsPixmapItem()
        self.line_item_hor_top = HLineItem()
        self.line_item_hor_bot = HLineItem()
        self.line_item_vert_left = VLineItem()
        self.line_item_vert_right = VLineItem()
        self.counter = 0
        self.calibration_running = False
        self.find_com_bool = False
        self.contours = []
        self.best_fit_line = []
        self.best_fit_line_plus = []
        self.best_fit_line_minus = []
        self.com = []
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
        self.signals.imageProcessingRequest.connect(self.new_request)
        self.signals.comOFF.connect(self.set_com_off)

    def set_com_off(self, o):
        if o:
            self.find_com_bool = False
        else:
            self.find_com_bool = True

    def new_request(self, calibration):
        self.calibration_running = calibration

    def find_center(self):
        upper_left = (self.line_item_vert_left.scenePos().x(),
                      self.line_item_hor_top.scenePos().y())
        lower_right = (self.line_item_vert_right.scenePos().x(),
                       self.line_item_hor_bot.scenePos().y())
        self.locate_jet(int(upper_left[0]), int(lower_right[0]),
                        int(upper_left[1]), int(lower_right[1]))
        if self.counter != 20:
            self.counter += 1
        elif self.counter == 20:
            self.counter = 0
            self.best_fit_line = []
            success = self.form_line(self.com, int(upper_left[1]), int(lower_right[1]))
            self.com = []
            if success and self.calibration_running:
                self.context.image_calibration_position(self.best_fit_line)
                self.signals.imageProcessingComplete.emit(True)
            elif not success and self.calibration_done:
                self.signals.imageProcessingComplete.emit(False)

    def locate_jet(self, x_start, x_end, y_start, y_end):
        crop = self.image[y_start:y_end, x_start:x_end]
        crop = cv2.convertScaleAbs(crop)
        self.contours, hierarchy = cv2.findContours(crop, cv2.RETR_EXTERNAL,
                                                    cv2.CHAIN_APPROX_SIMPLE, 
                                                    offset=(x_start, y_start)) 
        if len(self.contours) == 0:
            self.signals.message.emit("Was not able to find any contours. \n"
                                      "Try changing the ROI or image editing "
                                      "parameters")
        else:
            contours = []
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            empty = False
            while not empty:
                crop = cv2.erode(crop, kernel, iterations=1)
                c, h = cv2.findContours(crop, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE,
                                        offset=(x_start, y_start))
                for cont in c:
                    contours.append(cont)
                if len(c) == 0:
                    empty = True
            self.com += self.find_com(contours)
            return

    @staticmethod
    def find_com(contours):
        centers = []
        for i in range(len(contours)):
            M = cv2.moments(contours[i])
            if M['m00'] != 0:
                centers.append((int(M['m10']/M['m00']), int(M['m01']/M['m00'])))
        return centers

    def form_line(self, com, y_min, y_max):
        xypoints = list(zip(*com))
        y = np.asarray(list(xypoints[0]))
        x = np.asarray(list(xypoints[1]))
        res = stats.linregress(x, y)
        self.signals.message.emit(f"Slope: {res.slope:.6f}")
        self.signals.message.emit(f"Intercept: {res.intercept:.6f}")
        self.signals.message.emit(f"R-squared: {res.rvalue**2:.6f}")
        # for 95% confidence
        slope = res.slope
        intercept = res.intercept
        confidence_interval = 95
        pvalue = res.pvalue  # if p-value is > .1 get another image and try again
        slope_err = res.stderr
        intercept_err = res.intercept_stderr
        alpha = 1 - (confidence_interval / 100)
        critical_prob = 1 - alpha/2
        degrees_of_freedom = len(com) - 2
        tinv = lambda p, df: abs(stats.t.ppf(p/2., df))
        ts = tinv(alpha, degrees_of_freedom)
        y = np.append(y, [y_min, y_max])
        if slope:
            x_model = (y - intercept)*(1/slope)
            x_model_plus = (y - intercept - ts*intercept_err)*(1 / (slope + ts*slope_err))
            x_model_minus = (y - intercept + ts * intercept_err) * (1 / (slope - ts * slope_err))
            yl = list(y)
            i_max = yl.index(max(yl))
            i_min = yl.index(min(yl))
            self.best_fit_line = [(int(yl[i_min]), int(x_model[i_min])),
                                  (int(yl[i_max]), int(x_model[i_max]))]
            self.best_fit_line_plus = [(int(yl[i_min]), int(x_model_plus[i_min])),
                                       (int(yl[i_max]), int(x_model_plus[i_max]))]
            self.best_fit_line_minus = [(int(yl[i_min]), int(x_model_minus[i_min])),
                                        (int(yl[i_max]), int(x_model_minus[i_max]))]
            return True
        else:
            print("clearing best fit line... try again")
            self.best_fit_line = []
            self.best_fit_line_plus = []
            self.best_fit_line_minus = []
            return False

        # plt.plot(x, y, 'o', label='original data')
        # plt.plot(x, y_model, 'r', label='fitted line')
        # plt.plot(x, y_model_plus, 'b', label='fitted line error plus')
        # plt.plot(x, y_model_minus, 'g', label='fitted line error minus')
        # plt.legend()
        # plt.show()
        #return([(int(yl[i_min]), int(np.amin(x_model))),
        #        (int(yl[i_max]), int(np.amax(x_model)))],
        #       [(int(yl[i_min]), int(np.amin(x_model_plus))),
        #        (int(yl[i_max]), int(np.amax(x_model_plus)))],
        #       [(int(yl[i_min]), int(np.amin(x_model_minus))),
        #        (int(yl[i_max]), int(np.amax(x_model_minus)))])

    def update_image(self, im):
        # need to do something so that at the end of the calibration it also collects
        # multiple images.. also it just needs to be regularly finding the line if you want to
        # try to automate shut offs and such
        self.image = im
        self.image = cv2.convertScaleAbs(self.image)
        self.color_image = cv2.cvtColor(self.image, cv2.COLOR_GRAY2RGB)
        self.color_image = cv2.drawContours(self.color_image,
                                            self.contours, -1, (0, 255, 0), 3)
        if self.find_com_bool:    
            self.find_center()
            for point in self.com:
                self.color_image = cv2.circle(self.color_image, tuple(point), 1, (0, 255, 255))
            if len(self.best_fit_line):
                self.color_image = cv2.line(self.color_image, self.best_fit_line[1],
                                            self.best_fit_line[0], (0, 255, 255), 5)
            if len(self.best_fit_line_plus):
                self.color_image = cv2.line(self.color_image, self.best_fit_line_plus[1],
                                            self.best_fit_line_plus[0], (220,20,60), 2)
            if len(self.best_fit_line_minus):
                self.color_image = cv2.line(self.color_image, self.best_fit_line_minus[1],
                                            self.best_fit_line_minus[0], (220,20,60), 2)
        self.qimage = array2qimage(self.color_image)
        pixmap = QPixmap.fromImage(self.qimage) 
        self.pixmap_item.setPixmap(pixmap)
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

    def resizeEvent(self, event):
        if not self.pixmap_item.pixmap().isNull():
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_hor_top, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_vert_left, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_hor_bot, Qt.KeepAspectRatio)
            self.fitInView(self.line_item_vert_right, Qt.KeepAspectRatio)
        super(JetImageWidget, self).resizeEvent(event)
