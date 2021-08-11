from PyQt5.QtWidgets import QFrame
from gui.widgets.graphWidgetUi import Graphs_Ui
from PyQt5.QtCore import QTimer
import logging

log = logging.getLogger(__name__)


class GraphsWidget(QFrame, Graphs_Ui):

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
        self.timer = QTimer()
        self.refresh_rate = 0
        self.display_time = 0
        self.naverage = 0
        self.ave_cycle = []
        self.x_vals = []
        self.x_axis = []
        self.display_flag = None
        self.calibration_values = {}
        self.calibrated = False
        self.initialize_vals()
        self.setup_timer()
        self.connect_signals()

    def initialize_vals(self):
        self.refresh_rate = self.context.refresh_rate
        self.display_time = self.context.display_time
        self.naverage = self.context.graph_averaging
        self.ave_cycle = list(range(1, self.naverage+1))
        self.x_vals = self.context.x_axis
        self.x_axis = self.context.x_axis

    def connect_signals(self):
        # connect signals
        self.signals.refreshGraphs.connect(self.plot_data)
        self.signals.refreshAveValueGraphs.connect(self.plot_ave_data)
        self.signals.changeCalibrationValues.connect(self.calibrate)
        self.signals.changeDisplayTime.connect(self.set_display_time)
        self.signals.changeGraphAve.connect(self.set_graph_ave)
        self.signals.startTimer.connect(self.timer.start)
        self.signals.stopTimer.connect(self.timer.stop)
        self.signals.changeRefreshRate.connect(self.set_refresh_rate)
        self.signals.changeGraphAve.connect(self.set_graph_ave)

    def cycle_time(self):
        """
        used to ask the Status thread to send values to be plotted
        """
        if self.display_flag != None:
            if self.x_vals[0] == 0 and self.display_flag == 'display time':
                self.change_x_axis()
            elif self.ave_cycle[0] == 1 and self.display_flag == 'graph averaging':
                self.change_graph_averaging()
        self.ave_cycle.append(self.ave_cycle.pop(0))
        self.x_vals.append(self.x_vals.pop(0))
        if self.ave_cycle[-1] == self.naverage: #or self.x_vals[-1] == self.time_window:
            self.signals.askForValues.emit(self.x_vals[-1])
        else:
            self.signals.askForValues.emit(-1)
        if self.x_vals[0] == 0:
            self.signals.askForValues.emit(-2)

    def setup_timer(self):
        self.timer.setInterval(self.refresh_rate)
        self.timer.timeout.connect(self.cycle_time)

    def calibrate(self, cal):
        self.context.set_calibration_values(cal)
        self.signals.changeCalibrationDisplay.emit()
        self.calibration_values = cal
        length = len(self.x_axis)
        self.diff_low_range = list([self.calibration_values['diff']['range'][0]]*length)
        self.diff_high_range = list([self.calibration_values['diff']['range'][1]]*length)
        self.diff_mean = list([self.calibration_values['diff']['mean']]*length)
        self.i0_low_range = list([self.calibration_values['i0']['range'][0]] * length)
        self.i0_high_range = list([self.calibration_values['i0']['range'][1]] * length)
        self.i0_mean = list([self.calibration_values['i0']['mean']] * length)
        self.ratio_low_range = list([self.calibration_values['ratio']['range'][0]] * length)
        self.ratio_high_range = list([self.calibration_values['ratio']['range'][1]] * length)
        self.ratio_mean = list([self.calibration_values['ratio']['mean']] * length)
        if self.calibrated == True:
            self.refresh_plots()

        self.plot_calibration()
        self.context.set_calibrated(True)

    def refresh_plots(self):
        self.ratio_graph.refreshCalibrationPlots()
        self.i0_graph.refreshCalibrationPlots()
        self.diff_graph.refreshCalibrationPlots()

    def plot_data(self, buf):
        log.debug("This is the main thread still")
        self.ratio_graph.plt.setData(self.x_axis, buf['ratio'])
        self.i0_graph.plt.setData(self.x_axis, buf['i0'])
        self.diff_graph.plt.setData(self.x_axis, buf['diff'])

    def plot_calibration(self):
        self.diff_graph.percent_low.setData(self.x_axis,
                  self.diff_low_range)
        self.diff_graph.percent_high.setData(self.x_axis,
                  self.diff_high_range)
        self.diff_graph.mean_plt.setData(self.x_axis,
                  self.diff_mean)
        self.ratio_graph.percent_low.setData(self.x_axis,
                  self.ratio_low_range)
        self.ratio_graph.percent_high.setData(self.x_axis,
                  self.ratio_high_range)
        self.ratio_graph.mean_plt.setData(self.x_axis,
                  self.ratio_mean)
        self.i0_graph.percent_low.setData(self.x_axis,
                  self.i0_low_range)
        self.i0_graph.percent_high.setData(self.x_axis,
                  self.i0_high_range)
        self.i0_graph.mean_plt.setData(self.x_axis,
                  self.i0_mean)

    def plot_ave_data(self, data):
        self.ratio_graph.avg_plt.setData(data['time'], data['average ratio'], connect='finite')
        self.i0_graph.avg_plt.setData(data['time'], data['average i0'], connect='finite')
        self.diff_graph.avg_plt.setData(data['time'], data['average diff'], connect='finite')

    def set_refresh_rate(self, v):
        self.refresh_rate = v
        self.setup_timer()

    def set_graph_ave(self, a):
        self.naverage = a
        self.ave_cycle = (range(1, self.naverage + 1))

    def change_x_axis(self):
        self.x_axis = self.context.x_axis
        self.x_vals = self.context.x_axis
        self.ratio_graph.changeRange()
        self.i0_graph.changeRange()
        self.diff_graph.changeRange()
        self.display_flag = None

    def change_graph_averaging(self):
        self.ave_cycle = list(range(1, self.naverage + 1))
        self.display_flag = None

    def set_display_time(self, d):
        self.display_time = d
        self.change_display_flag('display time')

    def set_graph_ave(self, a):
        self.naverage = a
        self.change_display_flag('graph averaging')

    def change_display_flag(self, culprit):
        self.display_flag = culprit
        self.signals.message.emit("updating the graph ...")

