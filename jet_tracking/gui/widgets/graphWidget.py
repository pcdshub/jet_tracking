from PyQt5.QtWidgets import QFrame
from gui.widgets.graphWidgetUi import Graphs_Ui
import collections
import logging

log = logging.getLogger(__name__)


class GraphsWidget(QFrame, Graphs_Ui):

    def __init__(self, context, signals):
        super(GraphsWidget, self).__init__()
        self.signals = signals
        self.context = context
        print(self.context.calibrated)
        self.setupUi(self)
        self.signals.buffers.connect(self.plot_data)
        self.signals.avevalues.connect(self.plot_ave_data)
        self.signals.calibration_value.connect(self.calibrate)

    def calibrate(self, cal):
        self.context.set_calibration_values(cal)
        self.signals.display_calibration.emit()
        self.calibration_values = self.context.calibration_values
        if self.context.calibrated == True:
            self.refresh_plots()
        self.context.set_calibrated(True)

    def refresh_plots(self):
        self.ratio_graph.refreshCalibrationPlots()
        self.i0_graph.refreshCalibrationPlots()
        self.diff_graph.refreshCalibrationPlots()

    def plot_data(self, data):
        #log.debug("This is the main thread still")
        self.ratio_graph.plt.setData(list(data['time']), list(data['ratio']))
        self.ratio_graph.setXRange(list(data['time'])[0], list(data['time'])[-1])
        self.i0_graph.plt.setData(list(data['time']), list(data['i0']))
        self.diff_graph.plt.setData(list(data['time']), list(data['diff']))
        if self.context.calibrated == True:
            self.diff_graph.percent_low.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['diff']['range'][0]]*300, 300)))
            self.diff_graph.percent_high.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['diff']['range'][1]]*300, 300)))
            self.diff_graph.mean_plt.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['diff']['mean']]*300, 300)))
            self.ratio_graph.percent_low.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['ratio']['range'][0]]*300, 300)))
            self.ratio_graph.percent_high.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['ratio']['range'][1]]*300, 300)))
            self.ratio_graph.mean_plt.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['ratio']['mean']]*300, 300)))
            self.i0_graph.percent_low.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['i0']['range'][0]]*300, 300)))
            self.i0_graph.percent_high.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['i0']['range'][1]]*300, 300)))
            self.i0_graph.mean_plt.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['i0']['mean']]*300, 300)))

    def plot_ave_data(self, data):
        self.ratio_graph.avg_plt.setData(list(data['time']), list(data['average ratio']))
        self.i0_graph.avg_plt.setData(list(data['time']), list(data['average i0']))
        self.diff_graph.avg_plt.setData(list(data['time']), list(data['average diff']))
