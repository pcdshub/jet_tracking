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

x = np.arange(10)
y = np.arange(10)

class graphDisplay(object):

    def create_plots(self, *args):
        #####################################################################
        # set up user panel layout and give it a title
        # at this point it is assumed that there will be three graphs
        ####################################################################
        
        self.graph1 = args[0]
        self.graph2 = args[1]
        self.graph3 = args[2]

        p1 = self.graph1.plotItem
        p1.setLabels(left='Intensity', bottom='Initial Intensity')
        p1.setTitle(title = 'scattergram')
        p1.showGrid(x=True, y=True)
        self.scatter = pg.ScatterPlotItem(pen=pg.mkPen(width=5, color='r'), size = 1)
        self.graph1.addItem(self.scatter)
        
        
        self.p2 = self.graph2.plotItem
        self.p2.setLabels(left='Intensity', bottom=('Time', 's'))
        self.p2.setTitle(title = 'Initial Intensity')

        self.p3 = self.graph3.plotItem
        self.p3.setLabels(left='Initial Intensity', bottom=('Time', 's'))
        self.p3.setTitle(title = 'Diffraction Intensity') 
           
    def plot_scroll(self, data):
        if len(data[0]) > 125:
            self.scatter.setData(data[1][-125:], data[0][-125:])
        else:
            self.scatter.setData(data[1], data[0]) 
        #self.graph1.plot(data[0], data[1])
        if len(data[2]) > 120:
            self.graph2.setXRange(data[2][-120], data[2][-1])
    
        self.graph2.plot(data[2], data[0])

        self.graph3.setXLink(self.graph2)
        self.graph3.plot(data[2], data[1])
         
