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

    def __init__(self, graph1, graph2, graph3):
        
        self.graph1 = graph1
        self.graph2 = graph2
        self.graph3 = graph3
        self.create_plots()

    def create_plots(self):
        
        #self.plot1 = pg.plot(title = "data")
        self.graph1.setAxisItems({'bottom': pg.AxisItem('bottom', text="oh no")})
        
        #plot = pg.PlotDataItem(self.x, self.y)
        #self.graph1.plot(self.x, self.y, pen=3)
        #plotitem = self.graph1.plot()
        #plotitem.setLabel(axis = 'bottom', title = 'time(s)')
        #plotitem.addItem(plot)
        #viewbox = self.graph1.getViewBox() 
        #plotitem.addItem(plotitem)
        
        #self.graph1.addItem(plotitem)
        #print(plotitem.listDataItems())
        #####################################################################
        # set up user panel layout and give it a title
        ####################################################################
        # set up user panel layout and give it a title
        #self.graph1.addItem(self.plot1)
        #print(type(self.plot1))
    def plot_scroll(self, data):
         
        self.graph1.plot(data[0], data[1]) 
