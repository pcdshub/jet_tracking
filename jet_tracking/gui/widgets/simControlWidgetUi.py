from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, \
    QSlider, QPushButton
from PyQt5.Qt import Qt
from gui.widgets.basicWidgets import QRangeSlider
from gui.widgets.basicWidgets import QHLine

class Sim_Ui(object):

    def setupUi(self, obj):
        """
        used to setup the layout for the controls to the simulation
        """
        obj.layout_main = QVBoxLayout()
        obj.setLayout(obj.layout_main)
        obj.lbl_header = QLabel("Simulation Controls")

        obj.layout_main.addWidget(obj.lbl_header)


