import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from datastream import StatusThread
from collections import deque
import time

# PUT THESE FLOATING FUNCTION INSIDE A FILE IN THE TOOLS FOLDER
# SET SCROLLINGTIMEWIDGET TO ITS OWN WIDGET IN THE WIDGET FOLDER

def graph_setup(graph, title, y_axis, pen):
    graph.setTitle(title=title)
    graph.setLabels(left=y_axis, bottom="time (s)")
    graph.plotItem.showGrid(x=True, y=True)
    plot = pg.ScatterPlotItem(pen=pen, size=1)
    plot_average = pg.PlotCurveItem(pen=pg.mkPen(width=1, color='w'), size=1)
    graph.addPlot(plot)
    graph.addAvePlot(plot_average)

def add_calibration_graph(graph): 
    plot_mean = pg.PlotCurveItem(pen=pg.mkPen(width=1, color=(255, 165, 0)), size=1)
    plot_sigma_low = pg.PlotCurveItem(pen=pg.mkPen(width=1, color=(255, 255, 0)), \
                                          size=1, style=QtCore.Qt.DashLine)
    plot_sigma_high = pg.PlotCurveItem(pen=pg.mkPen(width=1, color=(255, 255, 0)), \
                                          size=1, style=QtCore.Qt.DashLine)
    graph.addMeanPlot(plot_mean)
    graph.addSigmaPlots(plot_sigma_low, plot_sigma_high)


class ScrollingTimeWidget(pg.PlotWidget):
    def __init__(self, context, signals, parent=None):
        super(ScrollingTimeWidget, self).__init__(parent)
        self.context = context
        self.signals = signals
        self.setMouseEnabled(x=False, y=False)
        self.setXRange(0, self.context.plot_time)
        #self.plt = pg.ScatterPlotItem()
        #self.avg_plt = pg.PlotCurveItem()
        #self.mean_plt = pg.PlotCurveItem()
        #self.percent_low = pg.PlotCurveItem()
        #self.percent_high = pg.PlotCurveItem()

    def addPlot(self, plt):
        self.plt = plt
        self.addItem(plt)

    def addAvePlot(self, plt):
        self.avg_plt = plt
        self.addItem(plt)

    def addMeanPlot(self, plt):
        self.mean_plt = plt
        self.addItem(plt)

    def addSigmaPlots(self, plt1, plt2):
        self.percent_low = plt1
        self.percent_high = plt2
        self.pfill = pg.FillBetweenItem(self.percent_high, self.percent_low, brush=(50, 50, 200, 50))
        self.addItem(self.percent_low)
        self.addItem(self.percent_high)
        self.addItem(self.pfill)

    def refreshCalibrationPlots(self):
        self.removeItem(self.percent_low)
        self.removeItem(self.percent_high)
        self.removeItem(self.mean_plt)
        self.addMeanPlot(self.mean_plt)
        self.addSigmaPlots(self.percent_low, self.percent_high)

