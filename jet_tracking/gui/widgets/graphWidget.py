from PyQt5.QtWidgets import QFrame
from gui.widgets.graphWidgetUi import Graphs_Ui
from PyQt5.QtCore import QTimer
import logging
import numpy as np

log = logging.getLogger(__name__)


class GraphsWidget(QFrame, Graphs_Ui):

    def __init__(self, context, signals):
        super(GraphsWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.initialize_vals()
        self.setup_timer()
        self.connect_signals()

    def initialize_vals(self):
        self.timer = QTimer()
        self.refresh_rate = self.context.thread_options['refresh rate']
        self.time_window = self.context.x_axis[-1]
        self.naverage = self.context.thread_options['averaging']
        self.avecycle = list(range(1, self.naverage+1))
        self.x_vals = self.context.x_axis

    def connect_signals(self):
        #connect signals
        self.signals.buffers.connect(self.plot_data)
        self.signals.avevalues.connect(self.plot_ave_data)
        self.signals.calibration_value.connect(self.calibrate)
        self.signals.start_timer.connect(self.timer.start)
        self.signals.stop_timer.connect(self.timer.stop)
        self.signals.refresh_rate.connect(self.update_refresh_rate)

    def cycle_time(self):
        """
        used to ask the Status thread to send values to be plotted
        """
        self.avecycle.append(self.avecycle.pop(0))
        self.x_vals.append(self.x_vals.pop(0))
        if self.avecycle[-1] == self.naverage: #or self.x_vals[-1] == self.time_window:
            self.signals.send_values.emit(self.x_vals[-1])
        else:
            self.signals.send_values.emit(-1)
        if self.x_vals[0] == 0:
            self.signals.send_values.emit(-2)

    def setup_timer(self):
        self.timer.setInterval(self.refresh_rate)
        self.timer.timeout.connect(self.cycle_time)

    def calibrate(self, cal):
        self.context.set_calibration_values(cal)
        self.signals.display_calibration.emit()
        self.calibration_values = cal
        length = len(self.context.x_axis)
        self.diff_low_range = list([self.calibration_values['diff']['range'][0]]*length)
        self.diff_high_range = list([self.calibration_values['diff']['range'][1]]*length)
        self.diff_mean = list([self.calibration_values['diff']['mean']]*length)
        self.i0_low_range = list([self.calibration_values['i0']['range'][0]] * length)
        self.i0_high_range = list([self.calibration_values['i0']['range'][1]] * length)
        self.i0_mean = list([self.calibration_values['i0']['mean']] * length)
        self.ratio_low_range = list([self.calibration_values['ratio']['range'][0]] * length)
        self.ratio_high_range = list([self.calibration_values['ratio']['range'][1]] * length)
        self.ratio_mean = list([self.calibration_values['ratio']['mean']] * length)
        if self.context.calibrated == True:
            self.refresh_plots()

        self.plot_calibration()
        self.context.set_calibrated(True)

    def refresh_plots(self):
        self.ratio_graph.refreshCalibrationPlots()
        self.i0_graph.refreshCalibrationPlots()
        self.diff_graph.refreshCalibrationPlots()

    def plot_data(self, buf):
        log.debug("This is the main thread still")
        self.ratio_graph.plt.setData(self.context.x_axis, buf['ratio'])
        self.i0_graph.plt.setData(self.context.x_axis, buf['i0'])
        self.diff_graph.plt.setData(self.context.x_axis, buf['diff'])

    def plot_calibration(self):
        self.diff_graph.percent_low.setData(self.context.x_axis,
                  self.diff_low_range)
        self.diff_graph.percent_high.setData(self.context.x_axis,
                  self.diff_high_range)
        self.diff_graph.mean_plt.setData(self.context.x_axis,
                  self.diff_mean)
        self.ratio_graph.percent_low.setData(self.context.x_axis,
                  self.ratio_low_range)
        self.ratio_graph.percent_high.setData(self.context.x_axis,
                  self.ratio_high_range)
        self.ratio_graph.mean_plt.setData(self.context.x_axis,
                  self.ratio_mean)
        self.i0_graph.percent_low.setData(self.context.x_axis,
                  self.i0_low_range)
        self.i0_graph.percent_high.setData(self.context.x_axis,
                  self.i0_high_range)
        self.i0_graph.mean_plt.setData(self.context.x_axis,
                  self.i0_mean)

    def plot_ave_data(self, data):
        self.ratio_graph.avg_plt.setData(data['time'], data['average ratio'], connect='finite')
        self.i0_graph.avg_plt.setData(data['time'], data['average i0'], connect='finite')
        self.diff_graph.avg_plt.setData(data['time'], data['average diff'], connect='finite')

    def update_refresh_rate(self, v):
        self.refresh_rate = v
        self.setup_timer()
