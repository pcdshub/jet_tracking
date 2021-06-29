import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from datastream import StatusThread
from collections import deque
import time

def graph_setup(graph, title, y_axis, pen):
    graph.setTitle(title=title)
    graph.setLabels(left=y_axis, bottom="time (s)")
    graph.plotItem.showGrid(x=True, y=True)
    plot = pg.ScatterPlotItem(pen=pen, size=1) 
    plot_average = pg.PlotCurveItem(pen=pg.mkPen(width=1, color='w'), size=1)
    plot_sigma_low = pg.PlotCurveItem(pen=pg.mkPen(width=1, color=(255, 255, 0)), \
                                          size=1, style=QtCore.Qt.DashLine)
    plot_sigma_high = pg.PlotCurveItem(pen=pg.mkPen(width=1, color=(255, 255, 0)), \
                                          size=1, style=QtCore.Qt.DashLine)
    graph.addPlot(plot)
    graph.addAvePlot(plot_average)
    graph.addSigmaPlots(plot_sigma_low, plot_sigma_high)


class ScrollingTimeWidget(pg.PlotWidget):
    def __init__(self, signals, parent=None):
        super(ScrollingTimeWidget, self).__init__(parent)

        self.SIGNALS = signals
        self.DATA_POINTS_TO_DISPLAY = 200
        self.setMouseEnabled(x=False, y=False)

    def addPlot(self, plt):
        self.plt = plt
        self.addItem(plt)

    def addAvePlot(self, plt):
        self.avePlt = plt
        self.addItem(plt)

    def addSigmaPlots(self, plt1, plt2):
        self.sigma_low = plt1
        self.sigma_high = plt2
        self.addItem(plt1)
        self.addItem(plt2)

