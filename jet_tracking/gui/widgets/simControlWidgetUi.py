from gui.widgets.basicWidgets import ComboBox, LineEdit
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                             QVBoxLayout)


class SimUi(object):

    def setupUi(self, obj):
        """
        used to setup the layout and initialize graphs
        """

        obj.layout = QVBoxLayout()
        obj.setLayout(obj.layout)

        obj.lbl_percent_drop = QLabel("Dropped Shots (%)")
        obj.box_percent_drop = LineEdit("10")
        obj.box_percent_drop.valRange(0, 100)
        obj.lbl_int = QLabel("Beam Intensity")
        obj.box_int = LineEdit("10")
        # obj.box_int.valRange(0, 100)
        obj.lbl_motor_pos = QLabel("Motor Position (mm)")
        obj.box_motor_pos = LineEdit("0")
        # obj.box_motor_pos.valRange(-1, 1)
        obj.lbl_jet_radius = QLabel("Jet Radius (mm)")
        obj.box_jet_radius = LineEdit("0.025")
        # obj.box_jet_radius.valRange(0, 0.1)
        obj.lbl_jet_center = QLabel("Jet Center (mm)")
        obj.box_jet_center = LineEdit("0.03")
        # obj.box_jet_center.valRange(-1, 1)
        obj.lbl_max_int = QLabel("Diffraction Intensity")
        obj.box_max_int = LineEdit("10")
        # obj.box_max_int.valRange(0, 100)
        obj.lbl_bg = QLabel("Background Noise")
        obj.box_bg = LineEdit("0.05")
        # obj.box_bg.valRange(0, 1)

        obj.layout_percent_drop = QHBoxLayout()
        obj.layout_percent_drop.addWidget(obj.lbl_percent_drop, 75)
        obj.layout_percent_drop.addWidget(obj.box_percent_drop)
        obj.layout_int = QHBoxLayout()
        obj.layout_int.addWidget(obj.lbl_int, 75)
        obj.layout_int.addWidget(obj.box_int)
        obj.layout_motor_pos = QHBoxLayout()
        obj.layout_motor_pos.addWidget(obj.lbl_motor_pos, 75)
        obj.layout_motor_pos.addWidget(obj.box_motor_pos)
        obj.layout_jet_radius = QHBoxLayout()
        obj.layout_jet_radius.addWidget(obj.lbl_jet_radius, 75)
        obj.layout_jet_radius.addWidget(obj.box_jet_radius)
        obj.layout_jet_center = QHBoxLayout()
        obj.layout_jet_center.addWidget(obj.lbl_jet_center, 75)
        obj.layout_jet_center.addWidget(obj.box_jet_center)
        obj.layout_max_int = QHBoxLayout()
        obj.layout_max_int.addWidget(obj.lbl_max_int, 75)
        obj.layout_max_int.addWidget(obj.box_max_int)
        obj.layout_bg = QHBoxLayout()
        obj.layout_bg.addWidget(obj.lbl_bg, 75)
        obj.layout_bg.addWidget(obj.box_bg)

        obj.layout.addLayout(obj.layout_percent_drop)
        obj.layout.addLayout(obj.layout_int)
        obj.layout.addLayout(obj.layout_motor_pos)
        obj.layout.addLayout(obj.layout_jet_radius)
        obj.layout.addLayout(obj.layout_jet_center)
        obj.layout.addLayout(obj.layout_max_int)
        obj.layout.addLayout(obj.layout_bg)
