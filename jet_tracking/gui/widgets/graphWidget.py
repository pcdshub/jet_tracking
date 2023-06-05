import logging

from gui.widgets.graphWidgetUi import GraphsUi
from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt
import numpy as np
from collections import deque
import pyqtgraph as pg

log = logging.getLogger(__name__)


class GraphsWidget(QFrame, GraphsUi):

    def __init__(self, context, signals):
        super(GraphsWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.display_time = self.context.display_time
        self.refresh_rate = self.context.refresh_rate
        self.num_points = self.display_time * self.refresh_rate
        self.x_axis = list(np.linspace(0, self.display_time, self.num_points))
        self.y_diff = deque([np.nan for _ in range(self.num_points)], self.num_points)
        self.y_i0 = deque([np.nan for _ in range(self.num_points)], self.num_points)
        self.y_ratio = deque([np.nan for _ in range(self.num_points)], self.num_points)
        self.y_ave = deque([np.nan for _ in range(self.num_points)], self.num_points)
        self.old_vals_diff = deque([], 2000)
        self.old_vals_i0 = deque([], 2000)
        self.old_vals_ratio = deque([], 2000)
        self.old_ave = deque([], 2000)
        self.diff_low_range = [np.nan for _ in range(self.num_points)]
        self.diff_high_range = [np.nan for _ in range(self.num_points)]
        self.diff_mean = [np.nan for _ in range(self.num_points)]
        self.i0_low_range = [np.nan for _ in range(self.num_points)]
        self.i0_high_range = [np.nan for _ in range(self.num_points)]
        self.i0_mean = [np.nan for _ in range(self.num_points)]
        self.ratio_low_range = [np.nan for _ in range(self.num_points)]
        self.ratio_high_range = [np.nan for _ in range(self.num_points)]
        self.ratio_mean = [np.nan for _ in range(self.num_points)]
        self.line_diff = self.graph1.plot(self.x_axis, list(self.y_diff), pen=None, symbol='o')
        self.line_i0 = self.graph2.plot(self.x_axis, list(self.y_i0), pen=None, symbol='o')
        self.line_ratio = self.graph3.plot(self.x_axis, list(self.y_ratio), pen=None, symbol='o')
        self.line_diff_low = self.graph1.plot(self.x_axis, list(self.diff_low_range),
                                              pen=pg.mkPen(width=1, color=(255, 255, 0)),
                                              size=1, style=Qt.DashLine)
        self.line_diff_high = self.graph1.plot(self.x_axis, list(self.diff_high_range),
                                               pen=pg.mkPen(width=1, color=(255, 255, 0)),
                                               size=1, style=Qt.DashLine)
        self.line_diff_mean = self.graph1.plot(self.x_axis, list(self.diff_mean),
                                               pen=pg.mkPen(width=1, color=(255, 165, 0)), size=1)
        self.line_i0_low = self.graph2.plot(self.x_axis, list(self.i0_low_range),
                                            pen=pg.mkPen(width=1, color=(255, 255, 0)),
                                            size=1, style=Qt.DashLine)
        self.line_i0_high = self.graph2.plot(self.x_axis, list(self.i0_high_range),
                                             pen=pg.mkPen(width=1, color=(255, 255, 0)),
                                             size=1, style=Qt.DashLine)
        self.line_i0_mean = self.graph2.plot(self.x_axis, list(self.i0_mean),
                                             pen=pg.mkPen(width=1, color=(255, 165, 0)), size=1)
        self.line_ratio_low = self.graph3.plot(self.x_axis, list(self.ratio_low_range),
                                               pen=pg.mkPen(width=1, color=(255, 255, 0)),
                                               size=1, style=Qt.DashLine)
        self.line_ratio_high = self.graph3.plot(self.x_axis, list(self.ratio_high_range),
                                                pen=pg.mkPen(width=1, color=(255, 255, 0)),
                                                size=1, style=Qt.DashLine)
        self.line_ratio_mean = self.graph3.plot(self.x_axis, list(self.ratio_mean),
                                                pen=pg.mkPen(width=1, color=(255, 165, 0)), size=1)
        self.line_ave = self.graph3.plot(self.x_axis, list(self.y_ave))
        self.calibration_values = {}
        self.display_flag = None
        self.calibrated = False
        self.connect_signals()

    def connect_signals(self):
        # connect signals
        self.signals.refreshGraphs.connect(self.plot_data)
        self.signals.changeCalibrationValues.connect(self.update_calibration_values)
        self.signals.changeDisplayTime.connect(self.set_display_time)
        self.signals.changeGraphAve.connect(self.set_graph_ave)
        self.signals.setNewXAxis.connect(self.set_new_axis)

    def update_calibration_values(self, cal):
        self.calibration_values = cal
        self.calibrate()

    def calibrate(self):
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
        self.plot_calibration()

    def plot_data(self, buf, count):
        if count == int(self.num_points*3/4):
            self.y_diff[count] = buf['diff']
            self.old_vals_diff.append(self.y_diff.popleft())
            self.y_diff.append(np.nan)
            self.y_i0[count] = buf['i0']
            self.old_vals_i0.append(self.y_i0.popleft())
            self.y_i0.append(np.nan)
            self.y_ratio[count] = buf['ratio'][-2]
            self.old_vals_ratio.append(self.y_ratio.popleft())
            self.y_ratio.append(np.nan)
            #self.y_ave[count] = buf['ratio'][-1]
            #self.old_ave.append(self.y_ave.popleft())
            #self.y_ave.append(np.nan)
        else:
            self.y_diff[count] = buf['diff']
            self.y_i0[count] = buf['i0']
            self.y_ratio[count] = buf['ratio'][-2]
            #self.y_ave[count] = buf['ratio'][-1]
        self.line_diff.setData(self.x_axis, list(self.y_diff))
        self.line_i0.setData(self.x_axis, list(self.y_i0))
        self.line_ratio.setData(self.x_axis, list(self.y_ratio))
        #self.line_ave.setData(self.x_axis, list(self.y_ave))

    def plot_calibration(self):
        self.line_diff_low.setData(self.x_axis, self.diff_low_range)
        self.line_diff_high.setData(self.x_axis, self.diff_high_range)
        self.line_diff_mean.setData(self.x_axis, self.diff_mean)
        self.line_i0_low.setData(self.x_axis, self.i0_low_range)
        self.line_i0_high.setData(self.x_axis, self.i0_low_range)
        self.line_i0_mean.setData(self.x_axis, self.i0_mean)
        self.line_ratio_low.setData(self.x_axis, self.ratio_low_range)
        self.line_ratio_high.setData(self.x_axis, self.ratio_high_range)
        self.line_ratio_mean.setData(self.x_axis, self.ratio_mean)

    def change_graph_averaging(self):
        self.ave_cycle = list(range(1, self.naverage + 1))
        self.signals.changeAverageSize.emit(self.naverage)
        self.display_flag = None

    def set_display_time(self, v):
        old_num_points = self.num_points
        new_display_time = int(v)
        new_num_points = int(new_display_time * self.refresh_rate)
        n_nan_old = int(old_num_points * 1/4)
        n_nan_new = int(new_num_points * 1/4)
        if old_num_points < new_num_points:
            new_points_diff = list(self.y_diff)[:int(new_num_points * 3/4)+1] + \
                                 [np.nan for _ in range(n_nan_new)]
            new_points_i0 = list(self.y_diff)[:int(new_num_points * 3/4)+1] + \
                               [np.nan for _ in range(n_nan_new)]
            new_points_ratio = list(self.y_diff)[:int(new_num_points * 3/4)+1] + \
                                  [np.nan for _ in range(n_nan_new)]
            n = new_num_points - len(new_points_diff)
            if len(self.old_vals_diff) >= n:
                for i in range(n):
                    new_points_diff.insert(0, self.old_vals_diff.pop())
                    new_points_i0.insert(0, self.old_vals_i0.pop())
                    new_points_ratio.insert(0, self.old_vals_ratio.pop())
            else:
                front_nan = n - len(self.old_vals_diff)
                for i in range(front_nan):
                    new_points_diff.insert(0, np.nan)
                    new_points_i0.insert(0, np.nan)
                    new_points_ratio.insert(0, np.nan)
                for i in range(n - front_nan):
                    new_points_diff.insert(0, self.old_vals_diff.pop())
                    new_points_i0.insert(0, self.old_vals_i0.pop())
                    new_points_ratio.insert(0, self.old_vals_ratio.pop())
        else:
            n = old_num_points - \
                (int(old_num_points*1/4) - int(new_num_points*1/4))
            points_diff = list(self.y_diff)[-n:]
            points_i0 = list(self.y_i0)[-n:]
            points_ratio = list(self.y_ratio)[-n:]
            new_points_diff = points_diff[:new_num_points+1]
            new_points_i0 = points_i0[:new_num_points+1]
            new_points_ratio = points_ratio[:new_num_points+1]
            for i in range(len(self.y_diff) - len(points_diff)):
                self.old_vals_diff.append(self.y_diff.popleft())
                self.old_vals_i0.append(self.y_i0.popleft())
                self.old_vals_ratio.append(self.y_ratio.popleft())
        if len(new_points_diff) < new_num_points:
            d = new_num_points - len(new_points_diff)
            new_points_diff = new_points_diff + [np.nan for _ in range(d)]
            new_points_i0 = new_points_i0 + [np.nan for _ in range(d)]
            new_points_ratio = new_points_ratio + [np.nan for _ in range(d)]
        self.y_diff = deque(new_points_diff[-new_num_points:], new_num_points)
        self.y_i0 = deque(new_points_i0[-new_num_points:], new_num_points)
        self.y_ratio = deque(new_points_ratio[-new_num_points:], new_num_points)
        idx = int(new_num_points*3/4)
        self.signals.setNewXAxis.emit(new_display_time, idx)

    def set_new_axis(self, axis, idx):
        self.display_time = axis
        self.num_points = self.display_time * self.refresh_rate
        self.x_axis = list(np.linspace(0, self.display_time, self.num_points))
        if self.calibrated:
            self.calibrate()

    def set_graph_ave(self, a):
        self.naverage = int(a)
        self.change_display_flag('graph averaging')

    def change_display_flag(self, culprit):
        self.display_flag = culprit
        self.signals.message.emit("updating the graph ...")
