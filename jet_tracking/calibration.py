import json
import os
import time
from os import path
from statistics import mean
from time import sleep

import cv2
import numpy as np
import pyqtgraph as pg
import zmq
from pydm import Display
from pydm.utilities import connection
from pydm.widgets import PyDMEmbeddedDisplay
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qtpy import QtCore
from qtpy.QtCore import QThread
from qtpy.QtWidgets import (QApplication, QFrame, QGraphicsItem,
                            QGraphicsRectItem, QGraphicsScene, QGraphicsView,
                            QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                            QPushButton, QScrollArea, QSizePolicy, QVBoxLayout,
                            QWidget)


class Calibration(object):

    def __init__(self, signals, Parent = None):

        self.parent = Parent
        self.signals = signals
        self.ave_low_i0 = 0
        self.mean_diff = 0
        self.sigma_diff = 0
        self.sigma_i0 = 0
        self.mean_ratio = 0
        values = [[],[],[]]

        self.signals.calibration.connect(self.monitor)

    def get_i0(self):

        return(self.ave_low_i0)

    def get_diff(self):

        return(self.mean_diff)

    def get_ratio(self):

        return(self.mean_ratio)

    def get_sigma(self):

        return(self.sigma_i0)

    def monitor(self):

        ### want to make Counter more flexible

        c = Counter(self.signals, 3600)

        t = time.time()

        c.start()
