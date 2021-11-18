import cv2
from PyQt5.QtWidgets import QFrame
from gui.widgets.editorWidgetUi import Editor_Ui
from datastream import JetImageFeed
import logging
from collections import deque

log = logging.getLogger(__name__)


class EditorWidget(QFrame, Editor_Ui):

    def __init__(self, context, signals):
        super(EditorWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.image_stream = JetImageFeed(self.context, self.signals)
        self.sliders = {'dilate': deque([None], 5), 
                        'erode': deque([None], 5),
                        'open': deque([None], 5),
                        'close': deque([None], 5),
                        'brightness': deque([None], 5),
                        'contrast': deque([None], 5),
                        'blur': deque([None], 5),
                        'left threshold': deque([0], 5),
                        'right threshold': deque([255], 5)}
        self.make_connections()
        self.dilate_off_on(True)
        self.open_off_on(True)

    def make_connections(self):
        self.bttn_cam_connect.clicked.connect(self.start_cam)
        self.bttn_cam_disconnect.clicked.connect(self.stop_cam)
        self.bttn_cam_calibrate.clicked.connect(self.calibrate)
        self.rd_bttn_dilate.clicked.connect(self.dilate_off_on)
        self.rd_bttn_erode.clicked.connect(self.erode_off_on)
        self.rd_bttn_open.clicked.connect(self.open_off_on)
        self.rd_bttn_close.clicked.connect(self.close_off_on)
        self.slider_dilate.sliderMoved.connect(self.set_dilate)
        self.slider_erode.sliderMoved.connect(self.set_erode)
        self.slider_open.sliderMoved.connect(self.set_open)
        self.slider_close.sliderMoved.connect(self.set_close)
        self.slider_brightness.sliderMoved.connect(self.set_brightness)
        self.slider_contrast.sliderMoved.connect(self.set_contrast)
        self.slider_blur.sliderMoved.connect(self.set_blur)
        self.range_slider_thresh.left_thumb_value_changed.connect(self.set_left_threshold)
        self.range_slider_thresh.right_thumb_value_changed.connect(self.set_right_threshold)

    def start_cam(self):
        self.context.open_cam_connection()
        if self.image_stream.connected:
            self.image_stream.start()
        else:
            print("Not connected")

    def stop_cam(self):
        self.image_stream.requestInterruption()
        self.image_stream.wait()

    def calibrate(self):
        if self.image_stream.connected:
            self.context.calibrate_image()
        else:
            self.signals.message.emit("The image feed is not live, try to connect camera")

    def set_dilate(self, v):
        self.sliders['dilate'].append(v)
        self.signals.imageProcessing.emit(self.sliders)

    def set_erode(self, v):
        self.sliders['erode'].append(v)
        self.signals.imageProcessing.emit(self.sliders)

    def set_open(self, v):
        self.sliders['open'].append(v)
        self.signals.imageProcessing.emit(self.sliders)

    def set_close(self, v):
        self.sliders['close'].append(v)
        self.signals.imageProcessing.emit(self.sliders)

    def set_contrast(self, v):
        self.sliders['contrast'].append(v)
        self.signals.imageProcessing.emit(self.sliders)

    def set_brightness(self, v):
        self.sliders['brightness'].append(v)
        self.signals.imageProcessing.emit(self.sliders)

    def set_blur(self, v):
        self.sliders['blur'].append(v)
        self.signals.imageProcessing.emit(self.sliders)

    def set_left_threshold(self, v):
        self.sliders['left threshold'].append(v)
        self.signals.imageProcessing.emit(self.sliders)

    def set_right_threshold(self, v):
        self.sliders['right threshold'].append(v)
        self.signals.imageProcessing.emit(self.sliders)

#    def adjust_image_dilation_erosion(self, v):
#        if self.imgray != []:
#            if v <= 5:
#                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
#                editim = cv2.erode(self.imgray, kernel, iterations = v)
#                self.signals.updateImage.emit(editim)
#            elif v > 5:
#                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
#                editim = cv2.dilate(self.imgray, kernel, iterations=v-5)
#                self.signals.updateImage.emit(editim)
#        else:
#            pass

    def dilate_off_on(self, enabled):
        self.slider_dilate.setEnabled(enabled)
        p = self.slider_dilate.sliderPosition()
        self.sliders['dilate'].append(p)
        self.rd_bttn_erode.setChecked(not enabled)
        self.slider_erode.setEnabled(not enabled)
        self.sliders['erode'].append(None)
        self.signals.imageProcessing.emit(self.sliders)

    def erode_off_on(self, enabled):
        self.slider_erode.setEnabled(enabled)
        p = self.slider_erode.sliderPosition()
        self.sliders['erode'].append(p)
        self.rd_bttn_dilate.setChecked(not enabled)
        self.slider_dilate.setEnabled(not enabled)
        self.sliders['dilate'].append(None)
        self.signals.imageProcessing.emit(self.sliders)

    def open_off_on(self, enabled):
        self.slider_open.setEnabled(enabled)
        p = self.slider_open.sliderPosition()
        self.sliders['open'].append(p)
        self.rd_bttn_close.setChecked(not enabled)
        self.slider_close.setEnabled(not enabled)
        self.sliders['close'].append(None)
        self.signals.imageProcessing.emit(self.sliders)

    def close_off_on(self, enabled):
        self.slider_close.setEnabled(enabled)
        p = self.slider_close.sliderPosition()
        self.sliders['close'].append(p)
        self.rd_bttn_open.setChecked(not enabled)
        self.slider_open.setEnabled(not enabled)
        self.sliders['open'].append(None)
        self.signals.imageProcessing.emit(self.sliders)



