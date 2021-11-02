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
                        'threshold': deque([None], 5)}
        self.make_connections()
        self.dilate_off_on(True)
        self.open_off_on(True)

    def make_connections(self):
        self.bttn_cam_connect.clicked.connect(self.start_cam)
        self.bttn_cam_disconnect.clicked.connect(self.stop_cam)
#        self.slider_dilate_erode.sliderMoved.connect(self.adjust_image_dilation_erosion)
        self.rd_bttn_dilate.clicked.connect(self.dilate_off_on)
        self.rd_bttn_erode.clicked.connect(self.erode_off_on)
        self.rd_bttn_open.clicked.connect(self.open_off_on)
        self.rd_bttn_close.clicked.connect(self.close_off_on)
        #self.slider_dilate.sliderMoved.connect(self.set_dilate)

    def start_cam(self):
        self.context.open_cam_connection()
        if self.image_stream.connected:
            self.image_stream.start()
        else:
            print("Not connected")

    def stop_cam(self):
        self.image_stream.requestInterruption()
        self.image_stream.wait()

#    def set_dilate(self, v):
        

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

    def update_image(self):
        self.image = self.context.image
        self.imgray = self.context.imgray

    def dilate_off_on(self, enabled):
        self.slider_dilate.setEnabled(enabled)
        self.rd_bttn_erode.setChecked(not enabled)
        self.slider_erode.setEnabled(not enabled)

    def erode_off_on(self, enabled):
        self.slider_erode.setEnabled(enabled)
        self.rd_bttn_dilate.setChecked(not enabled)
        self.slider_dilate.setEnabled(not enabled)

    def open_off_on(self, enabled):
        self.slider_open.setEnabled(enabled)
        self.rd_bttn_close.setChecked(not enabled)
        self.slider_close.setEnabled(not enabled)

    def close_off_on(self, enabled):
        self.slider_close.setEnabled(enabled)
        self.rd_bttn_open.setChecked(not enabled)
        self.slider_open.setEnabled(not enabled)



