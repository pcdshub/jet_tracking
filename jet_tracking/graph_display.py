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


class graphDisplay(object):
    
    def __init__(self, signals, calibration):
        
        self.signals = signals
        self.calibration = calibration
        self.intensityRatio = []
        self.aveIntensity = [[],[],[],[]]
        self.flaggedEvents = {'dropped_shot': [], 'missed_shot': []} 

        self.sigma = 1
        self.nsamp = 10
        self.irbelow = []

        self.signals.sigma.connect(self.update_sigma)
        self.signals.nsamp.connect(self.update_nsamp)

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
        
        self.plot2 = pg.PlotCurveItem(pen=pg.mkPen(width=2, color='b'), size = 1)
        self.graph2.addItem(self.plot2)
        self.plot2ave = pg.PlotCurveItem(pen=pg.mkPen(width=1, color='w'), size=1, style=Qt.DashLine)
        self.graph2.addItem(self.plot2ave)

        self.p3 = self.graph3.plotItem
        self.p3.setLabels(left='Initial Intensity', bottom=('Time', 's'))
        self.p3.setTitle(title = 'Diffraction Intensity') 
        
        self.plot3 = pg.PlotCurveItem(pen=pg.mkPen(width=2, color='g'), size = 1)
        self.graph3.addItem(self.plot3)
        self.plot3ave = pg.PlotCurveItem(pen=pg.mkPen(width=1, color='w'), size=1, style=Qt.DashLine)
        self.graph3.addItem(self.plot3ave)



    def plot_scroll(self, data):
        ratio = data[0][-1]/data[1][-1] 
        self.intensityRatio.append(ratio)

        if len(data[0]) > 121:
            #self.scatter.setData(data[1][-125:], data[0][-125:])
            self.scatter.setData(data[2][-121:], self.intensityRatio[-121:])
            self.plot2.setData(data[2][-121:], data[0][-121:])
            self.plot3.setData(data[2][-121:], data[1][-121:])

        else:
            #self.scatter.setData(data[1], data[0])
            self.scatter.setData(data[2], self.intensityRatio[-121:])
            self.plot2.setData(data[2], data[0])
            self.plot3.setData(data[2], data[1])
        
        self.graph2.setXLink(self.graph1)
        self.graph3.setXLink(self.graph1)

        self.moving_average(data)

    def moving_average(self, data):
        
        self.event_flagging(data)        
                
        if len(data[3]) % self.nsamp == 0:
            
            
            avep1 = mean(self.skimmer("dropped_shot", self.intensityRatio[-self.nsamp:]))
            avep2 = mean(self.skimmer("dropped_shot", data[0][-self.nsamp:]))
            avep3 = mean(data[1][-self.nsamp:])
            time = mean(data[2][-self.nsamp:])
            
            if len(self.aveIntensity[0]) > 121:
                for i in range(len(self.aveIntensity)):
                    self.aveIntensity[i].pop(0)

            self.aveIntensity[0].append(avep2)
            self.aveIntensity[1].append(avep3)
            self.aveIntensity[2].append(avep1)
            self.aveIntensity[3].append(time)
            self.plot2ave.setData(self.aveIntensity[3], self.aveIntensity[0])
            self.plot3ave.setData(self.aveIntensity[3], self.aveIntensity[1])
            
            self.check_status_update()

    def event_flagging(self,data):

        # is the gas detector intensity within 2sigma below the mean of calibrated i0
        # if so then flag it as a dropped shot

        # if not dropped shot but the downstream intensity is low then it's a missed shot
        # I/I0 falls below nsigma of the calibrated mean I/I0
        # if so then flag it as a missed shot
        # skimmer will write a new array that will exclude the dropped shots
        # generalize it so that you can differentiate based on any input - skim by whatever key you give it (dropped shots or missed shots)

        if len(self.flaggedEvents['dropped_shot']) > 120:
            self.flaggedEvents['dropped_shot'].pop(0)
        
        if len(self.flaggedEvents['missed_shot']) > 120:
            self.flaggedEvents['missed_shot'].pop(0)
        
        if self.intensityRatio[-1] < (self.calibration.get_meandiff() - self.sigma*self.calibration.get_sigma()):

            if data[0][-1] < (self.calibration.get_i0() - self.sigma):
            
                self.flaggedEvents['dropped_shot'].append(data[0][-1])
            else:

                self.flaggedEvents['missed_shot'].append(data[1][-1])


    def skimmer(self, key, oldlist):
    
        skimlist = list(i for i in oldlist if i not in self.flaggedEvents[key])
        
        return(skimlist)


    def check_status_update(self):
        
        self.cali_i0 = self.calibration.get_i0() - self.sigma
        checkValue = self.aveIntensity[0][-1]

        if len(self.irbelow) > 121: self.irbelow.pop(0)

        if checkValue < self.cali_i0:
            self.irbelow.append(1)
        else:
            self.irbelow.append(0)
        
        if sum(self.irbelow) > 10:
            #print("there has been 10 below now")
            self.signals.status.emit(2) #warning
        elif sum(self.irbelow) < 4:
            self.signals.status.emit(1) #tracking
        

    def update_sigma(self, sigma):
    
        self.sigma = sigma

    def update_nsamp(self, nsamp):

        self.nsamp = int(nsamp)



                
        
         
