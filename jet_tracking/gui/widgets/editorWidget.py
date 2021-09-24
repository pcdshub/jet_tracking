import cv2
from PyQt5.QtWidgets import QFrame
from gui.widgets.editorWidgetUi import Editor_Ui
import logging

log = logging.getLogger(__name__)


class EditorWidget(QFrame, Editor_Ui):

    def __init__(self, context, signals):
        super(EditorWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.image = []
        self.imgray = []
        self.make_connections()

    def make_connections(self):
        self.bttn_cam.clicked.connect(self.context.open_cam_connection)
        self.slider_dilate_erode.sliderMoved.connect(self.adjust_image_dilation_erosion)

    def adjust_image_dilation_erosion(self, v):
        self.update_image()
        if self.imgray != []:
            if v <= 5:
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
                editim = cv2.erode(self.imgray, kernel, iterations = v)
                self.signals.updateImage.emit(editim)
            elif v > 5:
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
                editim = cv2.dilate(self.imgray, kernel, iterations=v-5)
                self.signals.updateImage.emit(editim)
        else:
            pass

    def update_image(self):
        self.image = self.context.image
        self.imgray = self.context.imgray