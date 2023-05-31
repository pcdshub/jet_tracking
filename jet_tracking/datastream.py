import collections
import logging
import time
from statistics import StatisticsError, mean, stdev
import numpy as np
from ophyd import EpicsSignal
from epics import caget
from PyQt5.QtCore import QThread, QObject, QCoreApplication, QEventLoop
from pcdsdevices.epics_motor import Motor
from collections import deque
import cv2
import threading
from qimage2ndarray import array2qimage
from scipy import stats
from motorMoving import MotorAction
from tools.numGen import SimulationGenerator
from tools.simMotorMoving import SimulatedMotor
from tools.quickCalc import skimmer
from sketch.simJetImage import SimulatedImage


ologging = logging.getLogger('ophyd')
ologging.setLevel('DEBUG')

log = logging.getLogger("jet_tracker")
lock = threading.Lock()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(
                        *args, **kwargs)
        return cls._instances[cls]


class ValueReader(metaclass=Singleton):

    def __init__(self, context, signals):
        self.signals = signals
        self.context = context
        self.live_data = True
        self.live_initialized = False
        self.connected = False
        self.signal_diff = None
        self.signal_i0 = None
        self.signal_ratio = None
        self.signal_dropped = None
        self.simgen = None
        self.sim_vals = {"i0": 1, "diff": 1, "ratio": 1}
        self.diff = 1
        self.i0 = 1
        self.ratio = 1
        self.dropped = False
        self.make_connections()

    def make_connections(self):
        self.signals.changeRunLive.connect(self.run_live_data)

    def initialize_connections(self):
        """  Function for making connections when running in live mode.
        It should also handle the error that happens when you try to
        click start when the PVs are not active
        """
        if self.live_data:
            try:
                i0 = self.context.PV_DICT.get('i0', None)
                self.signal_i0 = EpicsSignal(i0)
                diff = self.context.PV_DICT.get('diff', None)
                self.signal_diff = EpicsSignal(diff)
                ratio = self.context.PV_DICT.get('ratio', None)
                self.signal_ratio = EpicsSignal(ratio)
                dropped = self.context.PV_DICT.get('dropped', None)
                self.signal_dropped = EpicsSignal(dropped)
            except NotImplementedError:
                pass
            else:
                self.live_initialized = True
                self.connected = True
        elif not self.live_data:
            self.simgen = SimulationGenerator(self.context, self.signals)
            self.connected = True

    def run_live_data(self, live):
        self.live_data = live

    def live_data_stream(self):
        if not self.live_initialized:
            # should not ever get here
            self.signals.message.emit("The live data"
                                      "stream is not working")
        self.i0 = self.signal_i0.get()
        self.diff = self.signal_diff.get()
        self.ratio = self.signal_ratio.get()

    def sim_data_stream(self):
        """Run with offline data"""
        # Adam's code for running simulations offline data
        # TODO: Add flag to enable this
        #
        # context_data = zmq.Context()
        # socket_data = context_data.socket(zmq.SUB)
        # socket_data.connect(''.join(['tcp://localhost:', '8123']))
        # socket_data.subscribe("")
        # while True:
        # md = socket_data.recv_json(flags=0)
        # msg = socket_data.recv(flags=0, copy=False, track=False)
        # buf = memoryview(msg)
        # data = np.frombuffer(buf, dtype=md['dtype'])
        # data = np.ndarray.tolist(data.reshape(md['shape']))
        # self.i0 = data[0]
        # self.diff = data[1]

        self.sim_vals = self.simgen.sim()
        self.i0 = self.sim_vals["i0"]
        self.diff = self.sim_vals["diff"]
        self.ratio = self.sim_vals["ratio"]
        self.dropped = self.sim_vals["dropped"]
        # self.motor_position = self.sim_vals["motor_position"]

    def read_value(self):  # needs to initialize first maybe using a decorator?
        log.debug("read value from ValueReader")
        if self.context.live_data:
            self.live_data_stream()
            return {'i0': self.i0, 'diff': self.diff, 'ratio': self.ratio,
                    'dropped': self.dropped}
        else:
            self.sim_data_stream()
            return {'i0': self.i0, 'diff': self.diff, 'ratio': self.ratio,
                    'dropped': self.dropped}


class StatusThread(QObject):
    def init_after_move(self, context, signals):
        """
        QThread which processes data and hands it to the main thread.

        After checking whether the current mode is either calibrating or
        running, values are obtained from the ValueReader. Dictionaries for
        buffers, buffer averages, and notable events for the initial intensity,
        diffraction intensity, and the ratio of these is built.

        parameters:
        ----------
        signals : object
        context : object
        """

        self.signals = signals
        self.context = context
        self.mode = "running"
        self.paused = True
        self.calibration_source = self.context.calibration_source
        self.calibration_priority = "recalibrate"
        self.num_cali = self.context.num_cali
        self.refresh_rate = self.context.refresh_rate
        self.percent = self.context.percent
        self.num_points = self.context.num_points
        self.graph_ave_time = self.context.graph_ave_time
        self.naverage = self.context.naverage
        self.averaging_size = self.context.averaging_size + 1
        self.notification_tolerance = self.context.notification_tolerance
        self.x_axis = self.context.x_axis
        self.bad_scan_limit = self.context.bad_scan_limit
        self.flag_message = None
        self.display_time = self.context.display_time
        self._count = 0
        self._ave_count = 0
        self.calibrated = False
        self.isTracking = False
        self.bad_scan_counter = 0
        self.status = ''
        self.display_flag = []
        self.cal_vals = [[], [], []]
        self.averages = {"i0": deque([0], 2000),
                         "diff": deque([0], 2000),
                         "ratio": deque([0], 2000),
                         "time": deque([0], 2000)}
        self.flagged_events = {
            "high intensity": deque([0], 2000),
            "missed shot": deque([0], 2000),
            "dropped shot": deque([0], 2000)}
        self.current_values = {"i0": 0, "diff": 0, "ratio": 0, "dropped": 0}
        self.buffers = {"i0": deque([np.nan], 2000),
                        "diff": deque([np.nan], 2000),
                        "ratio": deque([np.nan], 2000)}
        self.calibration_values = {'i0': {'mean': 0, 'stddev': 0,
                                          'range': (0, 0)},
                                   'diff': {'mean': 0, 'stddev': 0,
                                            'range': (0, 0)},
                                   'ratio': {'mean': 0, 'stddev': 0,
                                             'range': (0, 0)}}
        self.reader = ValueReader(self.context, self.signals)
        self.processor_worker = EventProcessor(self.signals)
        self.connect_signals()
        log.info("Initializing StatusThread")

    def connect_signals(self):
        self.signals.mode.connect(self.update_mode)
        self.signals.changeDisplayFlag.connect(self.change_display_flag)
        self.signals.changePercent.connect(self.set_percent)
        self.signals.changeCalibrationSource.connect(
            self.set_calibration_source)
        self.signals.changeNumberCalibration.connect(
            self.set_num_cali)
        self.signals.changeCalibrationPriority.connect(
            self.set_calibration_priority)
        self.signals.changeScanLimit.connect(
            self.set_scan_limit)
        self.signals.enableTracking.connect(self.tracking)
        self.signals.valuesRequest.connect(self.send_info_to_motor)
        self.signals.startStatusThread.connect(self.start_it)
        self.signals.stopStatusThread.connect(self.stop_it)
        self.signals.finishedMotorAlgorithm.connect(self.recalibrate)
        self.signals.setNewXAxis.connect(self.set_new_axis)

    def set_new_axis(self, axis, idx):
        self.display_time = axis
        self.num_points = self.display_time * self.refresh_rate
        self._count = idx

    def start_com(self):
        while not self.thread().isInterruptionRequested():
            QCoreApplication.processEvents(QEventLoop.AllEvents,
                                           int(self.refresh_rate*1000))
            self.run_data_thread()

    def start_it(self):
        log.info("Inside of the start_it method of StatusThread.")
        self.paused = False

    def stop_it(self, abort):
        self.paused = True
        if abort:
            self.thread().requestInterruption()
        else:
            pass

    def run_data_thread(self):
        """Long-running task to collect data points"""
        if not self.paused:
            self.current_values = self.reader.read_value()
            vals = self.current_values
            if self.mode == "running":
                self.update_buffer(vals)
                self.check_status_update()
                if self._ave_count == self.averaging_size:
                    self.calculate_averages()
                    vals['ratio'] = [vals['ratio'], self.averages['ratio'][-1]]
                else:
                    vals['ratio'] = [vals['ratio'], np.nan]
                self.signals.refreshGraphs.emit(vals, self._count)
            elif self.mode == "calibrate":
                self.calibrated = False
                self.update_buffer(vals)
                self.check_status_update()
                self.calibrate(vals)
                if self._ave_count == self.averaging_size:
                    self.calculate_averages()
                    vals['ratio'] = [vals['ratio'], self.averages['ratio'][-1]]
                else:
                    vals['ratio'] = [vals['ratio'], np.nan]
                self.signals.refreshGraphs.emit(vals, self._count)
            self._count += 1
            self._ave_count += 1
            if self._count > int(self.num_points*3/4):
                self._count = int(self.num_points*3/4)
            if self._ave_count > self.averaging_size-1:
                self._ave_count = 0
        time.sleep(1 / self.refresh_rate)

    def recalibrate(self):
        if self.calibration_priority == "recalibrate":
            self.mode = "calibrate"
        elif self.calibration_priority == "keep calibration":
            self.signals.message.emit("Calibration will not change. "
                                      "If you would like it to override this, "
                                      "select \"calibrate in gui\" and hit the "
                                      "calibrate button")

    def tracking(self, b):
        self.isTracking = b

    def update_mode(self, mode):
        log.info("Inside of the update_mode method of StatusThread.")
        self.mode = mode

    def set_percent(self, p):
        self.percent = p
        self.update_calibration_range()

    def set_calibration_source(self, c):
        self.calibration_source = c
    
    def set_num_cali(self, n):
        log.info("Inside of the set_num_cali method of StatusThread.")
        self.num_cali = n

    def set_calibration_priority(self, p):
        self.calibration_priority = p

    def set_scan_limit(self, sl):
        self.bad_scan_limit = sl

    def change_display_flag(self, culprit):
        if self.display_flag == "all":
            # this is to protect against making multiple changes and not
            # catching them
            pass
        else:
            self.display_flag = culprit
            self.signals.message.emit("updating the graph ...")

    def calculate_averages(self):
        try:
            i0 = self.buffers['i0'][-self.averaging_size:][~np.isnan(
                list(self.flagged_events['dropped shot'])[-self.averaging_size:])]
            diff = self.buffers['diff'][-self.averaging_size:][~np.isnan(
                list(self.flagged_events['dropped shot'])[-self.averaging_size:])]
            ratio = self.buffers['ratio'][-self.averaging_size:][~np.isnan(
                list(self.flagged_events['dropped shot'])[-self.averaging_size:])]
            avei0 = mean(list(i0))
            avediff = mean(list(diff))
            averatio = mean(list(ratio))
            vals = [avei0, avediff, averatio]
        except StatisticsError:
            vals = [0, 0, 0]
        self.averages['i0'].append(avei0)
        self.averages['diff'].append(avediff)
        self.averages['ratio'].append(averatio)

    def update_buffer(self, vals):
        """
        Add values from the ValueReader to the buffers dictionary.
        check if the events that came in should be flagged

        Keyword arguments:
        vals -- the values received from the ValueReader
        idx -- the current x index from the x_cycle list variable
        """
        v = [vals.get('diff'), vals.get('i0'),
             vals.get('ratio'), vals.get('dropped')]
        if self.calibrated:
            self.event_flagging(v)
        for k in self.buffers.keys():
            self.buffers[k].append(vals.get(k))

    def check_status_update(self):
        if self.calibrated:
            p = int(self.notification_tolerance + \
                 (self.notification_tolerance*0.5)) # plus 10% of notification tolerance
            miss = np.array(self.flagged_events['missed shot'])[-p:]
            drop = np.array(self.flagged_events['dropped shot'])[-p:]
            high = np.array(self.flagged_events['high intensity'])[-p:]
            n_miss = np.count_nonzero(miss[~np.isnan(miss)])
            n_drop = np.count_nonzero(drop[~np.isnan(drop)])
            n_high = np.count_nonzero(high[~np.isnan(high)])
            if n_miss > self.notification_tolerance:
                self.signals.changeStatus.emit("Warning, missed shots", "red")
                self.processor_worker.flag_counter('missed shot', 50,
                                                   self.missed_shots)
            elif n_drop > self.notification_tolerance:
                self.signals.changeStatus.emit("Lots of dropped shots",
                                               "yellow")
                self.processor_worker.flag_counter('dropped shot', 50,
                                                   self.dropped_shots)
            elif n_high > self.notification_tolerance:
                self.signals.changeStatus.emit("High Intensity", "orange")
                self.processor_worker.flag_counter('high intensity', 50,
                                                   self.high_intensity)
            else:
                if not self.processor_worker.isCounting:
                    self.signals.changeStatus.emit("Everything is good",
                                                   "green")
                    self.everything_is_good()
                if self.processor_worker.isCounting:
                    self.processor_worker.flag_counter("everything is good",
                                                       50,
                                                       self.everything_is_good)
        elif not self.calibrated:
            self.signals.changeStatus.emit("not calibrated", "orange")

    @staticmethod
    def normal_range(percent, sigma, vmean):
        """
        Used to find the upper and lower values on a normal distribution curve.

        Parameters
        ----------
        percent : int
            The percent represents the range of allowed values from the mean.
        sigma : float
            Sigma as provided by the calibration.
        vmean : float
            Mean as provided by the calibration.

        Returns
        -------
        a : float
            The lower value percent/2 away from the mean.
        b : float
            The upper value percent/2 away from the mean.
        """

        left = (1. - (percent/100.)) / 2.
        right = 1. - left
        zleft = stats.norm.ppf(left)
        zright = stats.norm.ppf(right)
        a = (zleft * sigma) + vmean
        b = (zright * sigma) + vmean
        return [a, b]

    def event_flagging(self, vals):
        """
        Flags values that are outside of the values indicated from the gui.

        Values that fall within the allowed range receive a value
        of zero in self.flagged_events deque. Otherwise, that position gets
        updated with the current value in the buffer.

        Parameters:
        vals
            Values from the ValueReader in the order i0, diff, ratio, x-axis.
        idx
            Current x index from the x_cycle list variable.
        """

        if self.calibrated:
            if vals[2] > self.calibration_values['ratio']['range'][1]:
                high_intensity = vals[2]
                self.flagged_events['high intensity'].append(high_intensity)
            else:
                high_intensity = 0
                self.flagged_events['high intensity'].append(high_intensity)
            if vals[2] < self.calibration_values['ratio']['range'][0]:
                missed_shot = vals[2]
                if missed_shot == 0:
                    missed_shot = 0.01
                self.flagged_events['missed shot'].append(missed_shot)
            else:
                missed_shot = 0
                self.flagged_events['missed shot'].append(missed_shot)
        if not vals[3]:
            dropped_shot = 0
            self.flagged_events['dropped shot'].append(dropped_shot)
        elif vals[3]:
            dropped_shot = 1
            self.flagged_events['dropped shot'].append(dropped_shot)

    def update_calibration_range(self):
        for name in ['i0', 'diff', 'ratio']:
            self.calibration_values[name]['range'] = self.normal_range(
                self.percent, self.calibration_values[name]['stddev'],
                self.calibration_values[name]['mean'])
        self.signals.changeCalibrationValues.emit(self.calibration_values)

    def set_calibration_values(self, name, vmean, std):
        self.calibration_values[name]['mean'] = vmean
        self.calibration_values[name]['stddev'] = std
        self.calibration_values[name]['range'] = self.normal_range(
            self.percent, self.calibration_values[name]['stddev'],
            self.calibration_values[name]['mean'])
        self.signals.changeCalibrationValues.emit(self.calibration_values)
        self.context.set_calibration_values(self.calibration_values)
        self.signals.changeCalibrationDisplay.emit()

    def calibrate(self, v):
        """
        Attempt to get new calibration values.

        Either gets the calibration values from the file created by the
        calibration shared memory process or it runs a calibration itself by
        averaging over a length of time (number of new events) and updates the
        calibration_values dictionary with the mean (or median), standard
        deviation, and range. If the calibration is successful, then the
        calibration is set to True, mode is set to running, and the
        calibration_values are updated.
        """

        if self.calibration_source == "calibration from results":
            results, cal_file = self.context.get_cal_results()
            if results is None:
                self.signals.message.emit("no calibration file there")
                self.calibrated = False
                self.mode = 'running'
            else:
                self.set_calibration_values('i0',
                                            float(results['i0_median']),
                                            float(results['i0_low']))
                # self.set_calibration_values('ratio',
                #                             float(results['med_ratio']),
                #                             float(results['ratio_low']))
                self.set_calibration_values('diff',
                                            float(results['int_median']),
                                            float(results['int_low']))
                # this should be removed
                ratio_low = float(results['int_low'])/float(results['i0_low'])
                self.set_calibration_values('ratio',
                                            float(results['med_ratio']),
                                            ratio_low)
                self.calibrated = True
                self.mode = 'running'
                self.signals.message.emit('calibration file: ' + str(cal_file))

        elif self.calibration_source == 'calibration in GUI':
            if not v.get('dropped'):
                self.cal_vals[0].append(v.get('i0'))
                self.cal_vals[1].append(v.get('diff'))
                self.cal_vals[2].append(v.get('ratio'))
            if len(self.cal_vals[0]) > self.num_cali:
                self.set_calibration_values('i0',
                                            mean(self.cal_vals[0]),
                                            stdev(self.cal_vals[0])
                                            )
                self.set_calibration_values('diff',
                                            mean(self.cal_vals[1]),
                                            stdev(self.cal_vals[1])
                                            )
                self.set_calibration_values('ratio',
                                            mean(self.cal_vals[2]),
                                            stdev(self.cal_vals[2])
                                            )
                self.update_calibration_range()
                self.mode = "running"
                self.calibrated = True
                self.cal_vals = [[], [], []]

        else:
            self.signals.message.emit('was not able to calibrate')
            self.calibrated = False
            self.mode = 'running'
        if self.calibrated:
            self.signals.message.emit(
                'i0 median: ' + str(self.calibration_values['i0']['mean']))
            self.signals.message.emit(
                'i0 low: ' + str(self.calibration_values['i0']['stddev']))
            self.signals.message.emit(
                'mean ratio: ' + str(self.calibration_values['ratio']['mean']))
            self.signals.message.emit(
                'standard deviation of the ratio: ' +
                str(self.calibration_values['ratio']['stddev']))

    def send_info_to_motor(self):
        self.signals.intensitiesForMotor.emit(self.current_values)

    def recalibrate(self):
        if self.calibration_priority == "keep calibration":
            self.signals.message.emit("The data may need to be recalibrated. "
                                      "There is consistently higher I/I0 than the "
                                      "calibration..")
        elif self.calibration_priority == "recalibrate":
            self.update_mode("calibrate")

    def missed_shots(self):
        if self.context.motor_running:
            if self.status == "everything is good":
                self.signals.notifyMotor.emit("missed shots")
            elif self.status == "dropped shots":
                self.signals.notifyMotor.emit("resume")
            elif self.status == "high intensity":
                self.signals.notifyMotor.emit("you downgraded")
        if self.isTracking and not self.context.motor_running:
            if self.bad_scan_counter < self.bad_scan_limit:
                self.signals.message.emit("lots of missed shots.. "
                                          "starting motor")
                self.context.update_motor_mode("run")
                self.bad_scan_counter += 1
            else:
                self.signals.enableTracking.emit(False)
                self.signals.trackingStatus.emit('disabled', "red")
        elif not self.isTracking and not self.context.motor_running:
            self.signals.message.emit("lots of missed shots.. consider running"
                                      " a search")
        if self.context.motor_running:
            if self.status == "everything is good":
                self.signals.notifyMotor.emit("missed shots")
            elif self.status == "dropped shots":
                self.signals.notifyMotor.emit("resume")
            elif self.status == "high intensity":
                self.signals.notifyMotor.emit("you downgraded")
        self.status = "missed_shots"

    def dropped_shots(self):
        if self.context.motor_running:
            self.signals.message.emit("lots of dropped shots.. pausing motor")
            self.signals.notifyMotor.emit("pause")
        self.status = "dropped shots"

    def high_intensity(self):
        self.bad_scan_counter = 0
        if self.context.motor_running:
            if self.status == "dropped shots":
                self.notifyMotor("resume")
            elif self.status == "missed shots":
                self.signals.notifyMotor.emit("high intensity")
            elif self.status == "everything is good":
                self.signals.notifyMotor.emit("you upgraded")
        self.status = "high intensity"

    def everything_is_good(self):
        self.bad_scan_counter = 0
        self.processor_worker.stop_count()
        if self.context.motor_running:
            if self.status == "dropped shots":
                self.signals.notifyMotor("resume")
            elif self.status == "missed shots":
                self.signals.notifyMotor.emit("Everything is good")
            elif self.status == "high intensity":
                self.signals.notifyMotor.emit("you downgraded")
        self.status = "everything is good"


class EventProcessor(QThread):
    def __init__(self, signals):
        super(EventProcessor, self).__init__()
        self.SIGNALS = signals
        self.flag_type = {}
        self.isCounting = False

    def flag_counter(self, new_flag, num_flagged, func_to_execute):
        self.isCounting = True
        if new_flag in self.flag_type.copy():
            self.flag_type[new_flag] += 1
            if num_flagged == self.flag_type[new_flag]:
                del(self.flag_type[new_flag])
                func_to_execute()
        else:
            self.flag_type[new_flag] = 1
        for key in self.flag_type.copy():
            if key != new_flag:
                self.flag_type[key] -= 1
                if self.flag_type[key] <= 0:
                    del(self.flag_type[key])

    def stop_count(self):
        self.flag_type = {}
        self.isCounting = False


class JetImageFeed(QThread):
    def __init__(self, context, signals):
        super(JetImageFeed, self).__init__()
        self.signals = signals
        self.context = context
        self.cam_name = ''
        self.dilate = None
        self.erode = None
        self.opener = None
        self.close = None
        self.contrast = None
        self.brightness = None
        self.blur = None
        self.left_threshold = 110
        self.right_threshold = 255
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        self.array_size_x_data = 0
        self.array_size_y_data = 0
        self.array_size_x_viewer = 0
        self.array_size_y_viewer = 0
        self.cam_array = ''
        self.refresh_rate = self.context.cam_refresh_rate
        self.signal_cam = None
        self.connected = False
        self.connect_signals()

    def connect_signals(self):
        self.signals.connectCam.connect(self.connect_cam)
        self.signals.imageProcessing.connect(self.update_editor_vals)
        self.signals.initializeCamValues.connect(self.update_cam_vals)

    def update_cam_vals(self):
        self.left_threshold = self.context.threshold

    def connect_cam(self):
        if self.context.live_data:
            self.cam_name = self.context.PV_DICT.get('camera', None)
            self.array_size_x_data = caget(self.cam_name +
                                           ':IMAGE1:ArraySize0_RBV')
            self.array_size_y_data = caget(self.cam_name +
                                           ':IMAGE1:ArraySize1_RBV')
            self.array_size_x_viewer = caget(self.cam_name +
                                             ':IMAGE2:ArraySize0_RBV')
            self.array_size_y_viewer = caget(self.cam_name +
                                             ':IMAGE2:ArraySize1_RBV')
            print(self.array_size_x_data, self.array_size_y_data, self.array_size_x_viewer)
            if (self.array_size_x_data != self.array_size_x_viewer or
                    self.array_size_y_data != self.array_size_y_viewer):
                self.signals.message.emit("ROI defined with markers in canViewer "
                                          "won't make sense because of different "
                                          "resolutions between the camera and "
                                          "camViewer")
            image = caget(self.cam_name + ':IMAGE1:ArrayData')
            print(image, type(image))
            if len(image) == 0:
                self.signals.message.emit("Can't read camera...")
                self.connected = False
            else:
                self.connected = True
            print(self.connected)
        else:
            self.cam_name = SimulatedImage(self.context, self.signals)
            self.array_size_y_viewer = self.cam_name.y_size
            self.array_size_x_viewer = self.cam_name.x_size
            image = self.cam_name.jet_im
            if not len(image):
                self.signals.message.emit("Simulated Image not working...")
                self.connected = False
            else:
                self.connected = True

    def update_editor_vals(self, e):
        self.dilate = e['dilate'][-1]
        self.erode = e['erode'][-1]
        self.opener = e['open'][-1]
        self.close = e['close'][-1]
        self.contrast = e['contrast'][-1]
        self.brightness = e['brightness'][-1]
        self.blur = e['blur'][-1]
        self.left_threshold = e['left threshold'][-1]
        self.right_threshold = e['right threshold'][-1]

    def editor(self, im):
        if self.dilate:
            im = cv2.dilate(im, self.kernel, iterations=self.dilate)
        if self.erode:
            im = cv2.erode(im, self.kernel, iterations=self.erode)
        if self.opener:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                               (self.opener, self.opener))
            im = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
        if self.close:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                               (self.close, self.close))
            im = cv2.morphologyEx(im, cv2.MORPH_CLOSE, kernel)
        if self.contrast:
            pass
        if self.brightness:
            pass
        if self.blur:
            im = cv2.GaussianBlur(im, (3, 3), self.blur)
        ret, im = cv2.threshold(im, self.left_threshold, self.right_threshold,
                                cv2.THRESH_BINARY)
        return im

    def run(self):
        while not self.isInterruptionRequested():
            if self.connected:
                if self.context.live_data:
                    image_array = caget(self.cam_name + ':IMAGE1:ArrayData')
                    image = np.reshape(image_array, (self.array_size_y_viewer,
                                           self.array_size_x_viewer))
                else:
                    self.cam_name.gen_image()
                    image = self.cam_name.jet_im
                image = cv2.convertScaleAbs(image)
                image = self.editor(image)
                self.signals.camImager.emit(image)
                time.sleep(1 / self.refresh_rate)
            else:
                print("you are not connected")
                time.sleep(1/self.refresh_rate)
        print("Interruption was requested: Image Thread")


class MotorThread(QObject):
    def init_after_move(self, context, signals):
        self.signals = signals
        self.context = context
        self.algorithm = self.context.algorithm
        self.low_limit = self.context.low_limit
        self.high_limit = self.context.high_limit
        self.step_size = self.context.step_size
        self.tolerance = self.context.position_tolerance
        self.calibration_values = self.context.calibration_values
        self.calibration_priority = "recalibrate"
        self.refresh_rate = self.context.refresh_rate
        self.moves = []
        self.intensities = []
        self.calibration_steps = 1
        self.vals = {}
        self.done = False
        self.motor_name = ''
        self.motor = None
        self.live = True
        self.connected = False
        self.wait = True
        self.mode = 'sleep'
        self.initial_position = 0
        self.averaging = 0
        self.request_new_values = False
        self.got_new_values = False
        self.request_image_processor = False
        self.complete_image_processor = False
        self.pix_per_mm = 0
        self.good_edge_points = []
        self.bad_edge_points = []
        self.sweet_spot = []
        self.max_value = 0
        self.paused = True
        self.action = MotorAction(self, self.context, self.signals)
        self.make_connections()

    def make_connections(self):
        self.signals.changeCalibrationPriority.connect(self.update_cp)
        self.signals.intensitiesForMotor.connect(self.update_values)
        self.signals.connectMotor.connect(self.connect_to_motor)
        self.signals.liveMotor.connect(self.live_motor)
        self.signals.notifyMotor.connect(self.impart_knowledge)
        self.signals.motorMode.connect(self.change_motor_mode)
        self.signals.imageProcessingComplete.connect(self.next_calibration_position)
        self.signals.startMotorThread.connect(self.start_it)
        self.signals.stopMotorThread.connect(self.stop_it)

    def check_motor_options(self):
        self.algorithm = self.context.algorithm
        self.low_limit = self.context.low_limit
        self.high_limit = self.context.high_limit
        self.step_size = self.context.step_size
        self.calibration_values = self.context.calibration_values
        self.refresh_rate = self.context.refresh_rate

    def start_com(self):
        log.info("Inside of the start_com method of MotorThread.")
        while not self.thread().isInterruptionRequested():
            self.run_motor_thread()
            QCoreApplication.processEvents(QEventLoop.AllEvents,
                                           int(self.refresh_rate*1000))

    def start_it(self):
        log.info("Inside of the start_it method of MotorThread.")
        self.paused = False

    def stop_it(self, abort):
        self.paused = True
        if abort:
            print('abort')
            self.thread().requestInterruption()
        else:
            print('Pause')

    def update_cp(self, p):
        self.calibration_priority = p

    def change_motor_mode(self, m):
        if m == 'sleep' and self.mode == 'run':
            self.signals.message.emit('Canceling motor moving immediately, going to sleep')
            self.mode = m
            self.paused = True
        if m == 'sleep' and self.mode == 'calibrate':
            self.signals.message.emit('calibration finished')
            self.mode = m
            self.paused = True
        if m == 'calibrate' and self.mode == 'sleep':
            self.signals.message.emit('starting image motor moving calibration')
            self.signals.message.emit("Initial motor position: " + str(self.initial_position))
            self.mode = m
            self.paused = False
        if m == 'calibrate' and self.mode == 'run':
            self.signals.message.emit('Calibrating while the mode is run should not be possible!!!')
        if m == 'run' and self.mode == 'calibrate':
            self.signals.message.emit('run while the mode is calibrate should not be possible!!!')
        if m == 'run' and self.mode == 'sleep':
            self.signals.message.emit('starting the algorithm you selected :)')
            self.signals.message.emit("Initial motor position: " + str(self.motor.position))
            if not self.connected:
                self.connect_to_motor()
            self.mode = m
            self.paused = False

    def move_to_input_position(self, mp):
        self.motor.move(mp, self.wait)
        self.signals.changeMotorPosition.emit(self.motor.position)

    def live_motor(self, live):
        self.live = live
        self.connect_to_motor()

    def connect_to_motor(self):
        if self.live:
            self.motor_name = self.context.PV_DICT.get('motor', None)
            print("connecting to: ", self.motor_name)
            try:
                self.motor = Motor(self.motor_name, name='jet_x')
                time.sleep(1)
                for i in self.motor.component_names:
                    print(f"{i} {getattr(self.motor, i).connected}")
            except NameError or NotImplementedError:
                self.connected = False
            else:
                self.context.update_motor_position(self.motor.position)
                self.connected = True
                self.wait = True
        elif not self.live:
            self.motor = SimulatedMotor(self.context, self.signals)
            self.context.update_motor_position(self.motor.position)
            self.connected = True
            self.wait = False

    def clear_values(self):
        self.moves = []
        self.done = False
        self.request_new_values = False
        self.got_new_values = False
        self.good_edge_points = []
        self.bad_edge_points = []
        self.sweet_spot = []
        self.max_value = 0

    def impart_knowledge(self, info):
        # ["resume", "everything is good", "you downgraded", "you upgraded",
        #  "pause", "missed shots", "high intensity"]
        print(info)
        if info == "everything is good":
            # if this info is passed then the status was changed from missed
            # shots to everything is good
            if len(self.moves) > 0:
                self.good_edge_points.append(self.moves[-1])
        if info == "resume":
            # if this info is passed then the status was changed from dropped
            # shots and the motor should resume
            self.paused = False
        if info == "you downgraded":
            # this is when the status is changed from high intensity to missed
            # shots
            pass
        if info == "you upgraded":
            # this is when the status is changed from missed shots to high
            # intensity
            pass
        if info == "pause":
            # if this info is passed then the status was changed to dropped
            # shots and the motor should pause
            self.paused = True
        if info == "missed shots":
            # this is when the status changes from everything is good to missed
            # shots
            if len(self.moves) > 0:
                self.bad_edge_points.append(self.moves[-1])
        if info == "high intensity":
            # this is when the status changes from everything is good to high
            # intensity
            self.sweet_spot.append(self.moves[-1])

    def next_calibration_position(self, success):
        if success:
            if self.calibration_steps == 1:
                self.initial_position = self.motor.position
            if self.calibration_steps >= 6:
                self.motor.move(self.initial_position - (self.step_size*(self.calibration_steps-5)), self.wait)
            else:
                self.motor.move(self.initial_position + (self.step_size * self.calibration_steps), self.wait)
            self.context.update_read_motor_position(self.motor.position)
            if not self.live:
                time.sleep((1/self.refresh_rate)*3)
            self.calibration_steps += 1
        self.complete_image_processor = True

    def update_image_calibration(self):
        # Assuming that the step size is in mm
        pix_per_mm = []
        image_calibration_positions = self.context.image_calibration_positions
        for i in range(len(image_calibration_positions)-1):
            motor_pos_diff = abs(image_calibration_positions[i+1][0] -
                                 image_calibration_positions[i][0])
            image_pos_diff = abs(image_calibration_positions[i+1][1][0][0] -
                                 image_calibration_positions[i][1][0][0])
            pix_per_mm.append(image_pos_diff/motor_pos_diff)
        self.pix_per_mm = mean(pix_per_mm)
        print(f"pix per mm: {self.pix_per_mm}")

    def update_values(self, vals):
        if not self.done:
            self.got_new_values = True
            self.check_motor_options()
            if vals != self.vals and vals['dropped'] is False:
                self.vals = vals
                self.average_intensity()
            else:
                pass

    def average_intensity(self):
        self.intensities += [self.vals['ratio'][0]]
        # this is where we set the integration time for each motor position
        # in the scan
        if len(self.intensities) == 20:
            print(self.intensities)
            self.check_motor_options()
            print(self.moves)

            # this should be the same either way
            self.moves.append([mean(self.intensities), self.motor.position])
            self.intensities = []
            if not self.paused:
                self.done, self.max_value = self.action.execute()

    def run_motor_thread(self):
        if not self.paused:
            if self.mode == 'run':
                if self.done:
                    if len(self.moves) > 4:
                        x = [a[1] for a in self.moves]
                        y = [b[0] for b in self.moves]
                        self.signals.plotMotorMoves.emit(self.motor.position, self.max_value, x, y)
                        print("go to sleep now..")
                        time.sleep(7)
                        self.signals.message.emit(f"Found peak intensity {self.max_value} "
                                                  f"at motor position: {self.motor.position}")
                        self.context.update_motor_position(self.motor.position)
                        self.context.update_motor_mode('sleep')
                        self.signals.finishedMotorAlgorithm.emit()
                else:
                    if self.request_new_values and self.got_new_values:
                        self.request_new_values = False
                        self.got_new_values = False
                    elif not self.request_new_values:
                        self.signals.valuesRequest.emit()
                        self.request_new_values = True
            elif self.mode == 'calibrate':
                if self.calibration_steps == 11:
                    self.motor.move(self.initial_position)
                    self.context.update_read_motor_position(self.motor.position)
                    time.sleep(1/self.refresh_rate*3)
                    self.signals.imageProcessingRequest.emit(False)
                    self.update_image_calibration()
                    self.context.image_calibration_positions = []
                    self.calibration_steps = 1
                    self.mode = 'sleep'
                    self.context.update_motor_mode('sleep')
                else:
                    if self.request_image_processor and self.complete_image_processor:
                        self.request_image_processor = False
                        self.complete_image_processor = False
                    elif not self.request_image_processor:
                        if not self.live:
                            time.sleep((1 / self.refresh_rate)*3)
                        self.signals.imageProcessingRequest.emit(True)
                        self.request_image_processor = True
            elif self.mode == 'sleep':
                self.clear_values()
        time.sleep(1/self.refresh_rate)
