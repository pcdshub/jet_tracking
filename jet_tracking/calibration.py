from time import sleep
from statistics import mean

from pydm import Display
from qtpy.QtCore import QThread
from os import path

import os
import json
import cv2
import numpy as np
import zmq

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from qtpy import QtCore
from pydm import Display
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QWidget, QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
    QGraphicsItem, QSizePolicy)
import pyqtgraph as pg

from pydm.widgets import PyDMEmbeddedDisplay
from pydm.utilities import connection

class Calibration(object):

    def __init__(self, signals):
        
        self.signals = signals
        self.ave_low_i0 = 0
        self.mean_diff = 0
        self.sigma_diff = 0
        self.sigma_i0 = 0        

    def get_i0(self):
        self.ave_low_i0 = 78
        return(self.ave_low_i0)


    def get_meandiff(self):
        self.mean_diff = 0.5
        return(self.mean_diff)
        
    def get_sigma(self):
        self.sigma_diff = 0.2
        return(self.sigma_diff)
