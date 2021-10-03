from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, \
    QSlider, QPushButton
from PyQt5.Qt import Qt
from gui.widgets.basicWidgets import QRangeSlider, QHLine

class Editor_Ui(object):

    def setupUi(self, obj):
        """
        used to setup the layout and initialize graphs
        """

        obj.layout = QVBoxLayout()
        obj.setLayout(obj.layout)

        obj.bttn_cam = QPushButton("Connect to Jet Cam")

        obj.lbl_morph = QLabel("Morphological Operations")

        obj.lbl_dilate_erode = QLabel("Dilate/Erode\nerodes or dilates edges")
        obj.slider_dilate_erode = QSlider(Qt.Horizontal)
        obj.slider_dilate_erode.setMinimum(0)
        obj.slider_dilate_erode.setMaximum(10)
        obj.slider_dilate_erode.setTickPosition(QSlider.TicksBelow)
        obj.slider_dilate_erode.setTickInterval(1)

        obj.lbl_open_close = QLabel("open/close\nopen is Erosion followed by Dilation\n"
                             "it is good for removing small blobs from an image\n"
                             "close is for dilation followed by erosion\n"
                             "it is good for closing holes inside of opbjects")
        obj.slider_open_close = QSlider(Qt.Horizontal)
        obj.slider_open_close.setMinimum(0)
        obj.slider_open_close.setMaximum(10)
        obj.slider_open_close.setTickPosition(QSlider.TicksBelow)
        obj.slider_open_close.setTickInterval(1)

        obj.lbl_brightness = QLabel("Brightness")
        obj.slider_brightness = QSlider(Qt.Horizontal)

        obj.lbl_contrast = QLabel("Contrast")
        obj.slider_contrast = QSlider(Qt.Horizontal)

        obj.lbl_blur = QLabel("Blur")
        obj.slider_blur = QSlider(Qt.Horizontal)

        obj.lbl_thresh = QLabel("Threshold")
        obj.range_slider_thresh = QRangeSlider(obj)

        obj.bttn_search = QPushButton("Search")
        obj.bttn_clear = QPushButton("Clear")
        obj.bttn_reset_all = QPushButton("Reset All")

        obj.layout_cam = QHBoxLayout()
        obj.layout_cam.addWidget(obj.bttn_cam)

        obj.layout_thresh = QHBoxLayout()
        obj.layout_thresh.addWidget(obj.lbl_thresh)
        obj.layout_thresh.addWidget(obj.range_slider_thresh)

        obj.layout_blur = QHBoxLayout()
        obj.layout_blur.addWidget(obj.lbl_blur)
        obj.layout_blur.addWidget(obj.slider_blur)

        obj.layout_brightness = QHBoxLayout()
        obj.layout_brightness.addWidget(obj.lbl_brightness)
        obj.layout_brightness.addWidget(obj.slider_brightness)

        obj.layout_contrast = QHBoxLayout()
        obj.layout_contrast.addWidget(obj.lbl_contrast)
        obj.layout_contrast.addWidget(obj.slider_contrast)

        obj.layout_bttns = QVBoxLayout()
        obj.layout_bttns.addWidget(self.bttn_search)
        obj.layout_bttns.addWidget(self.bttn_clear)
        obj.layout_bttns.addWidget(self.bttn_reset_all)

        obj.layout.addStretch()
        obj.layout.addLayout(obj.layout_cam)
        obj.hline0 = QHLine()
        obj.layout.addWidget(obj.hline0)
        obj.layout.addWidget(obj.lbl_dilate_erode)
        obj.layout.addWidget(obj.slider_dilate_erode)
        obj.hline1 = QHLine()
        obj.layout.addWidget(obj.hline1)
        obj.layout.addWidget(obj.lbl_open_close)
        obj.layout.addWidget(obj.slider_open_close)
        obj.hline2 = QHLine()
        obj.layout.addWidget(obj.hline2)
        obj.layout.addLayout(obj.layout_brightness)
        obj.layout.addLayout(obj.layout_contrast)
        obj.hline3 = QHLine()
        obj.layout.addWidget(obj.hline3)
        obj.layout.addLayout(obj.layout_blur)
        obj.hline4 = QHLine()
        obj.layout.addWidget(obj.hline4)
        obj.layout.addLayout(obj.layout_thresh)
        obj.hline5 = QHLine()
        obj.layout.addWidget(obj.hline5)
        obj.layout.addLayout(obj.layout_bttns)
        obj.layout.addStretch()
