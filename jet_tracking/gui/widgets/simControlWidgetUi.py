from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSizePolicy, QButtonGroup, QPushButton
from gui.widgets.basicWidgets import QRangeSlider, Label, LineEdit, ComboBox


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
        #  obj.box_int.valRange(0, 100)
        obj.lbl_motor_pos = QLabel("Motor Position (mm)")
        obj.box_motor_pos = LineEdit("0")
        #  obj.box_motor_pos.valRange(-1, 1)
        obj.lbl_jet_radius = QLabel("Jet Radius (mm)")
        obj.box_jet_radius = LineEdit("0.025")
        #  obj.box_jet_radius.valRange(0, 0.1)
        obj.lbl_jet_center = QLabel("Jet Center (mm)")
        obj.box_jet_center = LineEdit("0.03")
        #  obj.box_jet_center.valRange(-1, 1)
        obj.lbl_max_int = QLabel("Diffraction Intensity")
        obj.box_max_int = LineEdit("10")
        #  obj.box_max_int.valRange(0, 100)
        obj.lbl_bg = QLabel("Background Noise")
        obj.box_bg = LineEdit("0.05")
        #  obj.box_bg.valRange(0, 1)

        obj.cbox_sim_algorithm = ComboBox()
        obj.cbox_sim_algorithm.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        obj.cbox_sim_algorithm.addItem("Ternary Search")
        obj.cbox_sim_algorithm.addItem("Basic Scan")
        obj.cbox_sim_algorithm.addItem("Linear Scan")
        obj.bttn_start_tracking = QPushButton("Start Tracking")
        obj.bttn_start_tracking.setStyleSheet("\
            background-color: green;\
            font-size:16px;\
            ")
        obj.bttn_stop_tracking = QPushButton("Stop Tracking")
        obj.bttn_stop_tracking.setStyleSheet("\
            background-color: red;\
            font-size:16px;\
            ")

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

        obj.layout_algorithm = QHBoxLayout()
        obj.layout_algorithm.addWidget(obj.cbox_sim_algorithm)
        obj.layout_start = QHBoxLayout()
        obj.layout_start.addWidget(obj.bttn_start_tracking)
        obj.layout_stop = QHBoxLayout()
        obj.layout_stop.addWidget(obj.bttn_stop_tracking)

        obj.layout.addLayout(obj.layout_percent_drop)
        obj.layout.addLayout(obj.layout_int)
        obj.layout.addLayout(obj.layout_motor_pos)
        obj.layout.addLayout(obj.layout_jet_radius)
        obj.layout.addLayout(obj.layout_jet_center)
        obj.layout.addLayout(obj.layout_max_int)
        obj.layout.addLayout(obj.layout_bg)

        obj.layout.addLayout(obj.layout_algorithm)
        obj.layout.addLayout(obj.layout_start)
        obj.layout.addLayout(obj.layout_stop)
