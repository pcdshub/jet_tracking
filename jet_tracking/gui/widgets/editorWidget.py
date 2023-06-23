import logging
from collections import deque
import cv2
from datastream import JetImageFeed
from gui.widgets.editorWidgetUi import Editor_Ui
from PyQt5.QtWidgets import QFrame, QFileDialog
from PyQt5.QtCore import QThread

log = logging.getLogger(__name__)


class EditorWidget(QFrame, Editor_Ui):

    def __init__(self, context, signals):
        super(EditorWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.thread1 = QThread()
        self.worker_image = JetImageFeed()
        self.sliders = {'dilate': deque([None], 5),
                        'erode': deque([None], 5),
                        'open': deque([None], 5),
                        'close': deque([None], 5),
                        'brightness': deque([None], 5),
                        'contrast': deque([None], 5),
                        'blur': deque([None], 5),
                        'left threshold': deque([110], 5),
                        'right threshold': deque([255], 5)}
        self.make_connections()
        self.dilate_off_on(True)
        self.open_off_on(True)
        self.signals.initializeCamValues.emit()

    def make_connections(self):
        self.signals.terminateAll.connect(self.terminate_all)
        self.bttngrp1.buttonClicked.connect(self.check_button)
        self.bttn_cam_connect.clicked.connect(self.start_cam)
        self.bttn_cam_disconnect.clicked.connect(self.stop_cam)
        self.bttn_cam_calibrate.clicked.connect(self.calibrate)
        self.bttn_search.clicked.connect(self.search)
        self.signals.message.connect(self.display_message)
        self.bttn_reset_all.clicked.connect(self.reset_all)
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
        self.range_slider_thresh.left_thumb_value_changed.connect(
            self.set_left_threshold)
        self.range_slider_thresh.right_thumb_value_changed.connect(
            self.set_right_threshold)
        self.worker_image.moveToThread(self.thread1)
        self.worker_image.init_after_move(self.context, self.signals)
        self.thread1.started.connect(self.worker_image.start_comm)
        self.thread1.start()

    def start_cam(self):
        self.worker_image.connect_cam()
        if self.worker_image.connected:
            self.signals.startImageThread.emit()
        else:
            self.signals.message.emit("The image could not connect...")

    def stop_cam(self):
        if not self.worker_image.paused:
            self.signals.stopImageThread.emit(False)

    def check_button(self, bttn):
        bttn = bttn.text()
        if bttn == "COM detection off":
            self.context.set_com_on(False)
        if bttn == "COM detection on":
            self.context.set_com_on(True)

    def calibrate(self):
        if self.worker_image.connected and not self.worker_image.paused:
            self.context.calibrate_image()
        else:
            self.signals.message.emit("The image feed is not live or the" 
                                      "application is stopped try to connect" 
                                      "camera")
    
    def search(self):
        self.context.run_image_search()
    
    def reset_all(self):
        self.sliders = {'dilate': deque([None], 5),
                        'erode': deque([None], 5),
                        'open': deque([None], 5),
                        'close': deque([None], 5),
                        'brightness': deque([None], 5),
                        'contrast': deque([None], 5),
                        'blur': deque([None], 5),
                        'left threshold': deque([110], 5),
                        'right threshold': deque([255], 5)}
        self.signals.imageProcessing.emit(self.sliders)
    
    def display_message(self, message):
        pt = self.text_area.toPlainText()
        if pt.split('\n')[-1] == message.split('\n')[-1]:
            pass
        else:
            self.text_area.append(message)

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
        
    def terminate_all(self):
        self.signals.stopImageThread.emit(True)
        self.thread1.quit()
        self.thread1.wait()
