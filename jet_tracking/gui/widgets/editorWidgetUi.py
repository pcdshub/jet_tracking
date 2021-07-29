from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSlider
from gui.widgets.basicWidgets import QRangeSlider

class Editor_Ui(object):

    def setupUi(self, obj):
        """
        used to setup the layout and initialize graphs
        """

        obj.layout = QVBoxLayout(obj)
        obj.setLayout(self.layout)

        obj.lbl_thresh = QLabel("Threshold")
        obj.range_slider_thresh = QRangeSlider(obj)

        self.layout_thresh = QHBoxLayout()
        self.layout_thresh.addWidget(obj.lbl_thresh)
        self.layout_thresh.addWidget(obj.range_slider_thresh)

        obj.layout.addLayout(obj.layout_thresh)