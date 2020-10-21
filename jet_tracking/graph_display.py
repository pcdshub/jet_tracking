from time import sleep

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


class graphDisplay(object):

    def __init__(self, graph1, graph2, graph3):
        
        self.graph1 = graph1
        self.graph2 = graph2
        self.graph3 = graph3
        
        self.create_plots()

    def create_plots(self):

        #self.plot1 = pg.plot(title = "data")
        self.x = np.arange(100)
        self.y = np.arange(100)
        self.graph1.plot(title="did it work?")
        self.graph1.plot(self.x, self.y, pen=3)
        #self.graph1.plot().setLabels(bottom='time(s)', left='intensity')
         
        #self.graph1.addItem(self.plot1)
        #print(type(self.plot1))

