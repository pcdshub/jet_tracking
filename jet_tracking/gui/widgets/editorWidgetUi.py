from gui.widgets.basicWidgets import QHLine, QRangeSlider
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QRadioButton,
                             QSlider, QVBoxLayout, QButtonGroup)


class Editor_Ui(object):

    def setupUi(self, obj):
        """
        used to setup the layout and initialize graphs
        """
        obj.layout = QVBoxLayout()
        obj.setLayout(obj.layout)

        obj.bttngrp1 = QButtonGroup()
        obj.rd_bttn_gen_im = QRadioButton("Generate Image")
        obj.rd_bttn_gen_im.setChecked(True)
        obj.rd_bttn_sel_im = QRadioButton("Select Image")
        obj.bttngrp1.addButton(obj.rd_bttn_gen_im, id=0)
        obj.bttngrp1.addButton(obj.rd_bttn_sel_im, id=1)
        obj.bttngrp1.setExclusive(True)

        obj.bttn_cam_connect = QPushButton("Connect to Jet Cam")
        obj.bttn_cam_disconnect = QPushButton("Disconnect")
        obj.bttn_cam_calibrate = QPushButton("Calibrate")

        obj.lbl_morph = QLabel("Morphological Operations")

        obj.lbl_dilate = QLabel("Dilate edges")
        obj.slider_dilate = QSlider(Qt.Horizontal)
        obj.slider_dilate.setMinimum(0)
        obj.slider_dilate.setMaximum(10)
        obj.slider_dilate.setTickPosition(QSlider.TicksBelow)
        obj.slider_dilate.setTickInterval(1)

        obj.rd_bttn_dilate = QRadioButton("Dilate On/Off")
        obj.rd_bttn_dilate.setChecked(True)
        obj.rd_bttn_dilate.setAutoExclusive(False)

        obj.lbl_erode = QLabel("Erode edges")
        obj.slider_erode = QSlider(Qt.Horizontal)
        obj.slider_erode.setMinimum(0)
        obj.slider_erode.setMaximum(10)
        obj.slider_erode.setTickPosition(QSlider.TicksBelow)
        obj.slider_erode.setTickInterval(1)

        obj.rd_bttn_erode = QRadioButton("Erode On/Off")
        obj.rd_bttn_erode.setAutoExclusive(False)

        obj.lbl_open_close = QLabel("Open/Close\nOpening is Erosion followed "
                                    "by Dilation,\nit is good for removing "
                                    "small blobs from an image (remove salt "
                                    "noise).\nClose is Dilation followed by "
                                    "Erosion,\nit is good for closing holes "
                                    "inside of objects (remove pepper noise)"
                                    "\n\n")
        obj.lbl_open = QLabel("Open")
        obj.slider_open = QSlider(Qt.Horizontal)
        obj.slider_open.setMinimum(0)
        obj.slider_open.setMaximum(10)
        obj.slider_open.setTickPosition(QSlider.TicksBelow)
        obj.slider_open.setTickInterval(1)

        obj.rd_bttn_open = QRadioButton("Open On/Off")
        obj.rd_bttn_open.setChecked(True)
        obj.rd_bttn_open.setAutoExclusive(False)

        obj.lbl_close = QLabel("Close")
        obj.slider_close = QSlider(Qt.Horizontal)
        obj.slider_close.setMinimum(0)
        obj.slider_close.setMaximum(10)
        obj.slider_close.setTickPosition(QSlider.TicksBelow)
        obj.slider_close.setTickInterval(1)

        obj.rd_bttn_close = QRadioButton("Close On/Off")
        obj.rd_bttn_close.setAutoExclusive(False)

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

        obj.layout_image = QHBoxLayout()
        obj.layout_image.addWidget(obj.rd_bttn_gen_im)
        obj.layout_image.addWidget(obj.rd_bttn_sel_im)

        obj.layout_cam1 = QHBoxLayout()
        obj.layout_cam1.addWidget(obj.bttn_cam_connect)

        obj.layout_cam2 = QHBoxLayout()
        obj.layout_cam2.addWidget(obj.bttn_cam_disconnect)

        obj.layout_dilate = QHBoxLayout()
        obj.layout_dilate.addWidget(obj.slider_dilate)
        obj.layout_dilate.addWidget(obj.rd_bttn_dilate)

        obj.layout_erode = QHBoxLayout()
        obj.layout_erode.addWidget(obj.slider_erode)
        obj.layout_erode.addWidget(obj.rd_bttn_erode)

        obj.layout_close = QHBoxLayout()
        obj.layout_close.addWidget(obj.slider_close)
        obj.layout_close.addWidget(obj.rd_bttn_close)

        obj.layout_open = QHBoxLayout()
        obj.layout_open.addWidget(obj.slider_open)
        obj.layout_open.addWidget(obj.rd_bttn_open)

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
        obj.layout_bttns.addWidget(obj.bttn_search)
        obj.layout_bttns.addWidget(obj.bttn_clear)
        obj.layout_bttns.addWidget(obj.bttn_reset_all)

        obj.layout.addStretch()
        obj.layout.addLayout(obj.layout_image)
        obj.layout.addLayout(obj.layout_cam1)
        obj.layout.addLayout(obj.layout_cam2)
        obj.layout.addWidget(obj.bttn_cam_calibrate)
        obj.hline0 = QHLine()
        obj.layout.addWidget(obj.hline0)
        obj.layout.addWidget(obj.lbl_dilate)
        obj.layout.addLayout(obj.layout_dilate)
        obj.hline1 = QHLine()
        obj.layout.addWidget(obj.hline1)
        obj.layout.addWidget(obj.lbl_erode)
        obj.layout.addLayout(obj.layout_erode)
        obj.hline2 = QHLine()
        obj.layout.addWidget(obj.hline2)
        obj.layout.addWidget(obj.lbl_open)
        obj.layout.addLayout(obj.layout_open)
        obj.hline3 = QHLine()
        obj.layout.addWidget(obj.hline3)
        obj.layout.addWidget(obj.lbl_close)
        obj.layout.addLayout(obj.layout_close)
        # obj.hline4 = QHLine()
        # obj.layout.addWidget(obj.hline4)
        # obj.layout.addWidget(obj.lbl_open)
        # obj.layout.addWidget(obj.slider_open)
        obj.hline5 = QHLine()
        obj.layout.addWidget(obj.hline5)
        obj.layout.addLayout(obj.layout_brightness)
        obj.layout.addLayout(obj.layout_contrast)
        obj.hline6 = QHLine()
        obj.layout.addWidget(obj.hline6)
        obj.layout.addLayout(obj.layout_blur)
        obj.hline7 = QHLine()
        obj.layout.addWidget(obj.hline7)
        obj.layout.addLayout(obj.layout_thresh)
        obj.hline8 = QHLine()
        obj.layout.addWidget(obj.hline8)
        obj.layout.addLayout(obj.layout_bttns)
        obj.layout.addStretch()
