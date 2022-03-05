import logging

from gui.widgets.graphWidgetUi import GraphsUi
from PyQt5.QtWidgets import QFrame

log = logging.getLogger(__name__)


class GraphsWidget(QFrame, GraphsUi):

    def __init__(self, context, signals):
        super(GraphsWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.diff_low_range = []
        self.diff_high_range = []
        self.diff_mean = []
        self.i0_low_range = []
        self.i0_high_range = []
        self.i0_mean = []
        self.ratio_low_range = []
        self.ratio_high_range = []
        self.ratio_mean = []
        self.x_axis = []
        self.display_flag = None
        self.calibration_values = {}
        self.calibrated = False
        self.initialize_vals()
        self.connect_signals()

    def initialize_vals(self):
        self.display_time = self.context.display_time
        self.x_axis = self.context.x_axis

    def connect_signals(self):
        # connect signals
        self.signals.refreshGraphs.connect(self.plot_data)
        self.signals.refreshAveValueGraphs.connect(self.plot_ave_data)
        self.signals.changeCalibrationValues.connect(self.calibrate)
        self.signals.changeDisplayTime.connect(self.set_display_time)
        self.signals.changeGraphAve.connect(self.set_graph_ave)

    def calibrate(self, cal):
        self.context.set_calibration_values(cal)
        self.signals.changeCalibrationDisplay.emit()
        self.calibration_values = cal
        length = len(self.x_axis)
        self.diff_low_range = list(
            [self.calibration_values['diff']['range'][0]]*length)
        self.diff_high_range = list(
            [self.calibration_values['diff']['range'][1]]*length)
        self.diff_mean = list(
            [self.calibration_values['diff']['mean']]*length)
        self.i0_low_range = list(
            [self.calibration_values['i0']['range'][0]] * length)
        self.i0_high_range = list(
            [self.calibration_values['i0']['range'][1]] * length)
        self.i0_mean = list([self.calibration_values['i0']['mean']] * length)
        self.ratio_low_range = list(
            [self.calibration_values['ratio']['range'][0]] * length)
        self.ratio_high_range = list(
            [self.calibration_values['ratio']['range'][1]] * length)
        self.ratio_mean = list(
            [self.calibration_values['ratio']['mean']] * length)
        if self.calibrated:
            self.refresh_plots()
        self.plot_calibration()
        self.context.set_calibrated(True)

    def refresh_plots(self):
        self.ratio_graph.refreshCalibrationPlots()
        self.i0_graph.refreshCalibrationPlots()
        self.diff_graph.refreshCalibrationPlots()

    def plot_data(self, buf):
        self.ratio_graph.plt.setData(buf['time'], buf['ratio'])
        self.i0_graph.plt.setData(buf['time'], buf['i0'])
        self.diff_graph.plt.setData(buf['time'], buf['diff'])

    def plot_calibration(self):
        self.diff_graph.percent_low.setData(self.x_axis, self.diff_low_range)
        self.diff_graph.percent_high.setData(self.x_axis, self.diff_high_range)
        self.diff_graph.mean_plt.setData(self.x_axis, self.diff_mean)
        self.ratio_graph.percent_low.setData(self.x_axis, self.ratio_low_range)
        self.ratio_graph.percent_high.setData(self.x_axis,
                                              self.ratio_high_range)
        self.ratio_graph.mean_plt.setData(self.x_axis, self.ratio_mean)
        self.i0_graph.percent_low.setData(self.x_axis, self.i0_low_range)
        self.i0_graph.percent_high.setData(self.x_axis, self.i0_high_range)
        self.i0_graph.mean_plt.setData(self.x_axis, self.i0_mean)

    def plot_ave_data(self, data):
        self.ratio_graph.avg_plt.setData(data['time'], data['ratio'],
                                         connect='finite')
        self.i0_graph.avg_plt.setData(data['time'], data['i0'],
                                      connect='finite')
        self.diff_graph.avg_plt.setData(data['time'], data['diff'],
                                        connect='finite')

    def change_graph_averaging(self):
        self.ave_cycle = list(range(1, self.naverage + 1))
        self.signals.changeAverageSize.emit(self.naverage)
        self.display_flag = None

    def set_display_time(self, d):
        self.display_time = d
        self.ratio_graph.changeRange()
        self.i0_graph.changeRange()
        self.diff_graph.changeRange()
        self.set_x_axis()

    def set_x_axis(self):
        self.x_axis = self.context.x_axis
        if self.calibrated:
            self.calibrate(self.calibration_values)

    def set_graph_ave(self, a):
        self.naverage = int(a)
        self.change_display_flag('graph averaging')

    def change_display_flag(self, culprit):
        self.display_flag = culprit
        self.signals.message.emit("updating the graph ...")
