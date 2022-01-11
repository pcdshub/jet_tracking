import logging
import time
from statistics import mean, stdev, StatisticsError
from scipy import stats
import numpy as np
import collections
from ophyd import EpicsSignal
from epics import caget
from PyQt5.QtCore import QThread
from pcdsdevices.epics_motor import IMS
from sketch.num_gen import SimulationGenerator
from sketch.motorMoving import MotorAction
from sketch.sim_motorMoving import SimulatedMotor
from tools.quick_calc import skimmer
from collections import deque
import cv2
import threading
from qimage2ndarray import array2qimage

ologging = logging.getLogger('ophyd')
ologging.setLevel('DEBUG')

log = logging.getLogger(__name__)
log.setLevel('DEBUG')
lock = threading.Lock()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ValueReader(metaclass=Singleton):

    def __init__(self, context, signals):
        self.signals = signals
        self.context = context
        self.live_data = True
        self.live_initialized = False
        self.signal_diff = None
        self.signal_i0 = None
        self.signal_ratio = None
        self.signal_dropped = None
        self.simgen = SimulationGenerator(self.context, self.signals)
        self.sim_vals = {"i0": 1, "diff": 1, "ratio": 1}
        self.diff = 1
        self.i0 = 1
        self.ratio = 1
        self.dropped = False
        self.make_connections()

    def make_connections(self):
        self.signals.changeRunLive.connect(self.run_live_data)

    def initialize_live_connections(self):
        """  Function for making connections when running in live mode.
        It should also handle the error that happens when you try to
        click start when the PVs are not active
        """
        i0 = self.context.PV_DICT.get('i0', None)
        self.signal_i0 = EpicsSignal(i0)
        diff = self.context.PV_DICT.get('diff', None)
        self.signal_diff = EpicsSignal(diff)
        ratio = self.context.PV_DICT.get('ratio', None)
        self.signal_ratio = EpicsSignal(ratio)
        dropped = self.context.PV_DICT.get('dropped', None)
        self.signal_dropped = EpicsSignal(dropped)
        self.live_initialized = True

    def run_live_data(self, live):
        self.live_data = live

    def live_data_stream(self):
        if not self.live_initialized:
            self.initialize_live_connections()
        self.i0 = self.signal_i0.get()
        self.diff = self.signal_diff.get()
        self.ratio = self.signal_ratio.get()

    def sim_data_stream(self):
        """Run with offline data"""
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

        # Used for generating random simulated data
        # x = 0.8
        # y = 0.1
        # self.i0 = sinwv(x, 5000)
        # self.diff = sinwv(y, 2000)
        # try:
        #     self.ratio = self.i0/self.diff
        # except:
        #     self.ratio = self.ratio

        self.sim_vals = self.simgen.sim()
        self.i0 = self.sim_vals["i0"]
        self.diff = self.sim_vals["diff"]
        self.ratio = self.sim_vals["ratio"]
        self.dropped = self.sim_vals["dropped"]
        #self.motor_position = self.sim_vals["motor_position"]

    def read_value(self):  # needs to initialize first maybe using a decorator?
        if self.context.live_data:
            self.live_data_stream()
            return {'i0': self.i0, 'diff': self.diff, 'ratio': self.ratio, 'dropped': self.dropped}
        else:
            self.sim_data_stream()
            return {'i0': self.i0, 'diff': self.diff, 'ratio': self.ratio, 'dropped': self.dropped}

 
class StatusThread(QThread):

    def __init__(self, context, signals):
        super(StatusThread, self).__init__()
        """Child class of QThread which processes data and hands it to the main thread
        
        After checking whether the current mode is either calibrating or running,
        values are obtained from the ValueReader. Dictionaries for buffers,
        buffer averages, and notable events for the initial intensity, 
        diffraction intensity, and the ratio of these is built. 

        parameters:
        ----------
        signals : object
        context : object
        """
        self.signals = signals
        self.context = context
        self.calibration_source = ''
        self.flag_message = None
        self.refresh_rate = 0
        self.display_time = 0
        self.buffer_size = 0
        self.percent = 1
        self.averaging_size = 0
        self.notification_tolerance = 0
        self.graph_ave_time = 0
        self.count = 0
        self.naverage = 0
        self.ave_cycle = []
        self.ave_idx = []
        self.x_cycle = []
        self.x_axis = []
        self.calibrated = False
        self.isTracking = False
        self.badScanCounter = 0
        self.badScanLimit = 2
        self.mode = ''
        self.status = ''
        self.display_flag = []
        self.cal_vals = [[], [], []]
        self.calibration_values = {'i0': {'mean': 0, 'stddev': 0, 'range': (0, 0)},
                                   'diff': {'mean': 0, 'stddev': 0, 'range': (0, 0)},
                                   'ratio': {'mean': 0, 'stddev': 0, 'range': (0, 0)}}
        self.averages = {}
        self.buffers = {}
        self.current_values= {}
        self.flagged_events = {}
        self.create_value_reader()
        self.create_event_processor()
        self.create_vars()
        self.connect_signals()
        self.initialize_buffers()

        log.info("__init__ of StatusThread: %d" % QThread.currentThreadId())

    def create_vars(self):
        self.mode = "running"
        self.calibration_source = self.context.calibration_source
        self.refresh_rate = self.context.refresh_rate
        self.percent = self.context.percent
        self.buffer_size = self.context.buffer_size
        self.graph_ave_time = self.context.graph_ave_time
        self.naverage = self.context.naverage
        self.averaging_size = self.context.averaging_size+1
        self.notification_tolerance = self.context.notification_tolerance
        self.x_axis = self.context.x_axis
        self.ave_cycle = self.context.ave_cycle
        self.x_cycle = self.context.x_cycle
        self.ave_idx = self.context.ave_idx

    def create_value_reader(self):
        self.reader = ValueReader(self.context, self.signals)

    def create_event_processor(self):
        self.processor_worker = EventProcessor(self.context, self.signals)

    def initialize_buffers(self):
        # buffers and data collection

        self.averages = {"i0": deque([0], self.averaging_size),
                         "diff": deque([0], self.averaging_size),
                         "ratio": deque([0], self.averaging_size),
                         "time": deque([0], self.averaging_size)}
        self.flagged_events = {"high intensity": collections.deque([0] * self.buffer_size, self.buffer_size),
                              "missed shot": collections.deque([0] * self.buffer_size, self.buffer_size),
                              "dropped shot": collections.deque([0] * self.buffer_size, self.buffer_size)}
        self.current_values = {"i0": 0,"diff": 0,"ratio": 0,"dropped": 0}
        self.buffers = {"i0": deque([0], self.buffer_size),
                        "diff": deque([0], self.buffer_size),
                        "ratio": deque([0], self.buffer_size),
                        "time": deque([0], self.buffer_size)}

    def connect_signals(self):
        self.signals.mode.connect(self.update_mode)
        self.signals.changeDisplayFlag.connect(self.change_display_flag)
        self.signals.changePercent.connect(self.set_percent)
        self.signals.changeCalibrationSource.connect(self.set_calibration_source)
        self.signals.enableTracking.connect(self.tracking)
        self.signals.valuesRequest.connect(self.send_info_to_motor)

    @staticmethod
    def fix_size(old_size, new_size, b):
        d = new_size - old_size
        if d <= 0:
            for key in b:
                old = list(b[key])
                new = old[-d:]
                b[key] = deque(new, new_size)
        else:
            for key in b:
                old = list(b[key])
                b[key] = deque(old, new_size)
        return b

    @staticmethod
    def append_or_set(choice, d, vals, idx):
        """
        send in a list of vals in the order 'i0', 'diff', 'ratio' and 'time' and
        the choice to either "append" or "set" and
        the dictionary d and then execute the action

        Keyword arguments:
        choice -- either "append" or "set"
        d -- the dictionary that will be updated
        vals -- the values or value to be added
        idx -- the current x_cycle value
        """
        keys = list(d.keys())
        if choice == "append":
            for key, val in list(zip(keys, vals)):
                d[key].append(val)
        elif choice == "set":
            for key, val in list(zip(keys, vals)):
                d[key][idx] = val

    def tracking(self, b):
        self.isTracking = b

    def update_mode(self, mode):
        self.mode = mode

    def set_percent(self, p):
        self.percent = p
        self.update_calibration_range()

    def set_calibration_source(self, c):
        self.calibration_source = c

    def update_buffers_and_cycles(self):
        if self.display_flag == "all":
            self.signals.changeDisplayTime.emit(self.context.display_time)
            current_ave_size = self.averaging_size+1
            current_buff_size = self.buffer_size
            self.refresh_rate = self.context.refresh_rate
            self.buffer_size = self.context.buffer_size
            self.display_time = self.context.display_time
            self.naverage = self.context.naverage
            self.averaging_size = self.context.averaging_size
            self.x_axis = self.context.x_axis
            self.notification_tolerance = self.context.notification_tolerance
            self.ave_cycle = self.context.ave_cycle
            self.x_cycle = self.context.x_cycle
            self.ave_idx = self.context.ave_idx
            self.averages = self.fix_size(current_ave_size, self.averaging_size, self.averages)
            self.buffers = self.fix_size(current_buff_size, self.buffer_size, self.buffers)
            self.flagged_events = self.fix_size(current_buff_size, self.buffer_size, self.flagged_events)
            self.display_flag = None

        elif self.display_flag == "just average":
            current_ave_size = self.averaging_size+1
            self.graph_ave_time = self.context.graph_ave_time
            self.averaging_size = self.context.averaging_size
            self.naverage = self.context.naverage
            self.ave_cycle = self.context.ave_cycle
            self.ave_idx = self.context.ave_idx
            self.averages = self.fix_size(current_ave_size, self.averaging_size, self.averages)
            self.display_flag = None

    def change_display_flag(self, culprit):
        if self.display_flag == "all":
            # this is to protect against making multiple changes and not
            # catching them
            pass
        else:
            self.display_flag = culprit
            self.signals.message.emit("updating the graph ...")

    def check_cycle(self, x_idx, ave_cycle):
        """
        checks where the lists that track indices are at the moment
        returns a location code so that the graph will update correctly
        returns (-2) if the average should update, returns (0) if the
        x axis has cycled all the way back to the last value, and returns (-1)
        at any other point in time.
        """
        if x_idx == 0 and self.display_flag:
            self.update_buffers_and_cycles()
        elif ave_cycle == 0 and self.display_flag == "just average":
            self.update_buffers_and_cycles()
        if x_idx == self.buffer_size-1:
            return 0
        elif ave_cycle == self.naverage:
            return -2
        else:
            return -1

    def points_to_plot(self, x_idx, ave_cycle, ave_idx):
        """
        makes list of values to be plotted on the
        graph and sends the values through the refresh graphs signal
        checks if the location info indicates that the average needs to
        be updated on the graph (0) or if the end of the buffer has been
        reached (-2)
        - sets a nan value if the end of the buffer has been reached so that
        there is a break in the plotting. See plot_ave_data function in
        graph widget and notice that it says "connect='finite' and look
        that up for more info
        """
        location_info = self.check_cycle(x_idx, ave_cycle)  # returns info to inform what to plot
        i0 = list(self.buffers['i0'])
        diff = list(self.buffers['diff'])
        ratio = list(self.buffers['ratio'])
        t = list(self.buffers['time'])
        buff = {'i0': i0, 'diff': diff, 'ratio': ratio, 'time': t}
        self.signals.refreshGraphs.emit(buff)
        if location_info == 0:
            self.update_averages(ave_idx, x_idx)
            ave_idx = self.ave_idx[0]
            if ave_idx > len(list(self.averages['i0'])) - 1:
                choice = "append"
            else:
                choice = "set"
            vals = [float("NaN"), float("NaN"), float("NaN"), float("NaN")]
            self.append_or_set(choice, self.averages, vals, ave_idx)
            self.ave_idx.append(self.ave_idx.pop(0))

        elif location_info == -2:
            self.update_averages(ave_idx, x_idx)

    def update_averages(self, ave_idx, x_idx):
        if ave_idx > len(list(self.averages['i0']))-1:
            choice = "append"
        else:
            choice = "set"
        try:
            if self.calibrated and len(self.flagged_events['dropped shot']) == len(self.buffers['i0']):
                avei0 = mean(skimmer('dropped shot',
                                     list(self.buffers['i0']), self.flagged_events)[:-self.naverage])
                avediff = mean(skimmer('dropped shot',
                                       list(self.buffers['diff']), self.flagged_events)[:-self.naverage])
                averatio = mean(skimmer('dropped shot',
                                        list(self.buffers['ratio']), self.flagged_events)[:-self.naverage])
            else:
                avei0 = mean(list(self.buffers['i0'])[:-self.naverage])
                avediff = mean(list(self.buffers['diff'])[:-self.naverage])
                averatio = mean(list(self.buffers['ratio'])[:-self.naverage])
            vals = [avei0, avediff, averatio, self.x_axis[x_idx]]
        except StatisticsError:
            vals = [0, 0, 0, self.x_axis[x_idx]]
        self.append_or_set(choice, self.averages, vals, ave_idx)
        i0 = list(self.averages['i0'])
        diff = list(self.averages['diff'])
        ratio = list(self.averages['ratio'])
        t = list(self.averages['time'])
        ave = {"i0": i0, "diff": diff,
               "ratio": ratio, 'time': t}
        self.ave_idx.append(self.ave_idx.pop(0))
        self.signals.refreshAveValueGraphs.emit(ave)

    def update_buffer(self, vals, idx):
        """
        Add values from the ValueReader to the buffers dictionary.
        check if the events that came in should be flagged

        Keyword arguments:
        vals -- the values received from the ValueReader
        idx -- the current x index from the x_cycle list variable
        """
        if idx > len(list(self.buffers['i0']))-1:
            choice = "append"
        else:
            choice = "set"
        v = [vals.get('i0'), vals.get('diff'), vals.get('ratio'), self.x_axis[idx]]
        self.append_or_set(choice, self.buffers, v, idx)
        v = [vals.get('i0'), vals.get('diff'), vals.get('ratio'), vals.get('dropped')]
        if self.calibrated and choice == "set":
            self.event_flagging(v, idx)

    def run(self):
        """Long-running task to collect data points"""
        while not self.isInterruptionRequested():
            new_values = self.reader.read_value()
            self.current_values = new_values
            x_idx = self.x_cycle[0]
            ave_cycle = self.ave_cycle[0]
            ave_idx = self.ave_idx[0]
            self.ave_cycle.append(self.ave_cycle.pop(0))
            self.x_cycle.append(self.x_cycle.pop(0))
            if self.mode == "running":
                self.update_buffer(new_values, x_idx)
                self.check_status_update()
                self.points_to_plot(x_idx, ave_cycle, ave_idx)
                time.sleep(1/self.refresh_rate)
            elif self.mode == "calibrate":
                self.calibrated = False
                self.update_buffer(new_values, x_idx)
                self.points_to_plot(x_idx, ave_cycle, ave_idx)
                self.calibrate(new_values)
                time.sleep(1 / self.refresh_rate)
        print("Interruption request: %d" % QThread.currentThreadId())

    def check_status_update(self):
        if self.calibrated:
            if np.count_nonzero(self.flagged_events['missed shot']) > self.notification_tolerance:
                self.signals.changeStatus.emit("Warning, missed shots", "red")
                self.processor_worker.flag_counter('missed shot', 50, self.missed_shots)
            elif np.count_nonzero(self.flagged_events['dropped shot']) > self.notification_tolerance:
                self.signals.changeStatus.emit("Lots of dropped shots", "yellow")
                self.processor_worker.flag_counter('dropped shot', 50, self.dropped_shots)
            elif np.count_nonzero(self.flagged_events['high intensity']) > self.notification_tolerance:
                self.signals.changeStatus.emit("High Intensity", "orange")
                self.processor_worker.flag_counter('high intensity', 50, self.high_intensity)
            else:
                if not self.processor_worker.isCounting:
                    self.signals.changeStatus.emit("Everything is good", "green")
                    self.everything_is_good()
                if self.processor_worker.isCounting:
                    self.processor_worker.flag_counter('everything is good', 50, self.everything_is_good)
        elif not self.calibrated:
            self.signals.changeStatus.emit("not calibrated", "orange")

    @staticmethod
    def normal_range(percent, sigma, vmean):
        """ Used to find the upper and lower values on a normal distribution curve
        Parameters
        ----------
        percent:
                 the percent represents the range of allowed values from the mean
        sigma:
                 sigma as provided by the calibration
        vmean:
                 mean as provided by the calibration
        returns
        -------
        a: float
                 the lower value percent/2 away from the mean
        b: float
                 the upper value percent/2 away from the mean
        """
        left = (1. - (percent/100.)) / 2.
        right = 1. - left
        zleft = stats.norm.ppf(left)
        zright = stats.norm.ppf(right)
        a = (zleft * sigma) + vmean
        b = (zright * sigma) + vmean
        return [a, b]

    def event_flagging(self, vals, idx):
        """ The method of flagging values that are outside of the values indicated
        from the gui. Values that fall within the allowed range receive a value of
        zero in self.flagged_events deque. Otherwise, that position gets updated with
        the current value in the buffer.

        Keyword arguments:
        vals -- the values from the ValueReader in the order i0, diff, ratio, x-axis
        idx -- the current x index from the x_cycle list variable
        """
        if self.calibrated:
            if vals[2] > self.calibration_values['ratio']['range'][1]:
                high_intensity = vals[2]
                self.flagged_events['high intensity'][idx] = high_intensity
            else:
                high_intensity = 0
                self.flagged_events['high intensity'][idx] = high_intensity
            if vals[2] < self.calibration_values['ratio']['range'][0]:
                missed_shot = vals[2]

                # added to fix issue with dropped shots
                # revisit if there's anything weird    
                if missed_shot == 0:
                    missed_shot = 0.01
                # print("missed shot: ", missed_shot)
                self.flagged_events['missed shot'][idx] = missed_shot
            else:
                missed_shot = 0
                self.flagged_events['missed shot'][idx] = missed_shot
        if not vals[3]:
            dropped_shot = 0
            self.flagged_events['dropped shot'][idx] = dropped_shot
        elif vals[3]:
            dropped_shot = 1
            self.flagged_events['dropped shot'][idx] = dropped_shot

    def update_calibration_range(self):
        for name in ['i0', 'diff', 'ratio']:
            self.calibration_values[name]['range'] = self.normal_range(self.percent,
                                                                       self.calibration_values[name]['stddev'],
                                                                       self.calibration_values[name]['mean'])
        self.signals.changeCalibrationValues.emit(self.calibration_values)

    def set_calibration_values(self, name, vmean, std):
        self.calibration_values[name]['mean'] = vmean
        self.calibration_values[name]['stddev'] = std
        self.calibration_values[name]['range'] = self.normal_range(self.percent,
                                                                   self.calibration_values[name]['stddev'],
                                                                   self.calibration_values[name]['mean'])
        self.signals.changeCalibrationValues.emit(self.calibration_values)
        self.context.set_calibration_values(self.calibration_values)

    def calibrate(self, v):
        """
        Either gets the calibration values from the file created by the calibration shared memory process
        or it runs a calibration itself by averaging over a length of time (number of new events) and updates
        the calibration_values dictionary with the mean (or median), standard deviation, and range.
        If the calibration is successful, then the calibration is set to True, mode is set to running,
        and the calibration_values are updated.
        """
        if self.calibration_source == "calibration from results":
            results, cal_file = self.context.get_cal_results()  # change the experiment
            if results == None:
                self.signals.message.emit("no calibration file there")
                self.calibrated = False
                self.mode= 'running'
            else:
                self.set_calibration_values('i0', 
                                        float(results['i0_median']),
                                        float(results['i0_low'])
                                        )
                #self.set_calibration_values('ratio', 
                #                        float(results['med_ratio']),
                #                        float(results['ratio_low'])
                #                        )
                self.set_calibration_values('diff', 
                                        float(results['int_median']),
                                        float(results['int_low'])
                                        )
                # this should be removed
                ratio_low = float(results['int_low'])/float(results['i0_low'])
                self.set_calibration_values('ratio', float(results['med_ratio']), ratio_low)
                self.calibrated = True
                self.mode = 'running'
                self.signals.message.emit('calibration file: ' + str(cal_file))

        elif self.calibration_source == 'calibration in GUI':
            if v.get('dropped') != True:
                self.cal_vals[0].append(v.get('i0'))
                self.cal_vals[1].append(v.get('diff'))
                self.cal_vals[2].append(v.get('ratio'))
            if len(self.cal_vals[0]) > 50:
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
                self.calibrated = True
                self.cal_vals = [[], [], []]
                self.mode = "running"

        else:
            self.signals.message.emit('was not able to calibrate')
            self.calibrated = False
            self.mode = 'running'
        if self.calibrated:    
            self.signals.message.emit('i0 median: ' + str(self.calibration_values['i0']['mean']))
            self.signals.message.emit('i0 low: ' + str(self.calibration_values['i0']['stddev']))
            self.signals.message.emit('mean ratio: ' + str(self.calibration_values['ratio']['mean']))
            self.signals.message.emit('standard deviation of the ratio: ' + str(self.calibration_values['ratio']['stddev']))

    def send_info_to_motor(self):
        self.signals.intensitiesForMotor.emit(self.current_values)

    def recalibrate(self):
        self.signals.message.emit("The data may need to be recalibrated. There is consistently higher I/I0 than the calibration..")
        self.signals.sleepMotor.emit()
 
    def missed_shots(self):
        if self.isTracking and not self.context.motor_running:
            if self.badScanCounter < self.badScanLimit:
                self.signals.message.emit("lots of missed shots.. starting motor")
                self.signals.wakeMotor.emit()
                self.badScanCounter += 1
            else:
                self.signals.enableTracking.emit(False)
                self.signals.trackingStatus.emit('disabled', "red")
        elif not self.isTracking and not self.context.motor_running:
            self.signals.message.emit("lots of missed shots.. consider running a search")
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
        self.badScanCounter = 0
        if self.context.motor_running:
            if self.status == "dropped shots":
                self.notifyMotor("resume")
            elif self.status == "missed shots":
                self.signals.notifyMotor.emit("high intensity")
            elif self.status == "everything is good":
                self.signals.notifyMotor.emit("you upgraded")
        self.status = "high intensity"

    def everything_is_good(self):
        self.badScanCounter = 0
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
    def __init__(self, context, signals):
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
        self.opene = None
        self.close = None
        self.contrast = None
        self.brightness = None
        self.blur = None
        self.left_threshold = None
        self.right_threshold = None
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
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

    def connect_cam(self):
        self.cam_name = self.context.PV_DICT.get('camera', None)
        self.array_size_x_data = caget(self.cam_name + ':IMAGE1:ArraySize0_RBV')
        self.array_size_y_data = caget(self.cam_name + ':IMAGE1:ArraySize1_RBV')
        self.array_size_x_viewer = caget(self.cam_name + ':IMAGE2:ArraySize0_RBV')
        self.array_size_y_viewer = caget(self.cam_name + ':IMAGE2:ArraySize1_RBV')
        if self.array_size_x_data != self.array_size_x_viewer or \
                self.array_size_y_data != self.array_size_y_viewer:
            self.signals.message.emit("ROI defined with markers in canViewer won't make sense because of "
                                      "different resolutions between the camera and camViewer")
        image = caget(self.cam_name + ':IMAGE1:ArrayData')
        if len(image) == 0:
            self.signals.message.emit("Can't read camera...")
            self.connected = False
        else:
            self.connected = True

    @staticmethod
    def fix_image(im, x, y):
        im = np.reshape(im, (x, y))
        return im

    def update_editor_vals(self, e):
        self.dilate = e['dilate'][-1]
        self.erode = e['erode'][-1]
        self.opene = e['open'][-1]
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
        if self.opene:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.opene, self.opene))
            im = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
        if self.close:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.close, self.close))
            im = cv2.morphologyEx(im, cv2.MORPH_CLOSE, kernel)
        if self.contrast:
            pass
        if self.brightness:
            pass
        if self.blur:
            pass
        ret, im = cv2.threshold(im, self.left_threshold, self.right_threshold, cv2.THRESH_BINARY)
        return(im)

    def run(self):
        while not self.isInterruptionRequested():
            if self.connected:
                image = caget(self.cam_name + ':IMAGE2:ArrayData')
                image = self.fix_image(image, self.array_size_x_viewer, self.array_size_y_viewer)
                image = self.editor(image)
                qimage = array2qimage(image)
                self.signals.camImage.emit(qimage)
                time.sleep(1/self.refresh_rate)
            else:
                print("you are not connected")
                time.sleep(1/self.refresh_rate)
        print("Interruption was requested: Image Thread")


class MotorThread(QThread):
    def __init__(self, context, signals):
        super(MotorThread, self).__init__()
        self.signals = signals
        self.context = context
        self.moves = []
        self.intensities = []
        self.vals = {}
        self.done = False
        self.motor_name = ''
        self.motor = None
        self.live = True
        self.calibration_values = {}
        self.algorithm = ''
        self.low_limit = 0
        self.high_limit = 0
        self.step_size = 0
        self.tolerance = 0
        self.averaging = 0
        self.refresh_rate = 0
        self.request_new_values = False
        self.got_new_values = False
        self.good_edge_points = []
        self.bad_edge_points = []
        self.sweet_spot = []
        self.max_value = 0
        self.pause = False
        self.action = MotorAction(self, self.context, self.signals)
        self.create_vars()
        self.make_connections()

    def create_vars(self):
        """ sets the motor options from Context"""
        self.algorithm = self.context.algorithm
        self.low_limit = self.context.low_limit
        self.high_limit = self.context.high_limit
        self.step_size = self.context.step_size
        self.tolerance = self.context.position_tolerance
        self.calibration_values = self.context.calibration_values
        self.refresh_rate = self.context.refresh_rate

    def check_motor_options(self):
        self.algorithm = self.context.algorithm
        self.low_limit = self.context.low_limit
        self.high_limit = self.context.high_limit
        self.step_size = self.context.step_size
        self.calibration_values = self.context.calibration_values
        self.refresh_rate = self.context.refresh_rate

    def make_connections(self):
        self.signals.intensitiesForMotor.connect(self.update_values)
        self.signals.connectMotor.connect(self.connect_to_motor)
        self.signals.liveMotor.connect(self.live_motor)
        self.signals.notifyMotor.connect(self.impart_knowledge)

    def live_motor(self, live):
        self.live = live

    def connect_to_motor(self):
        if self.live:
            # should have a catch here for if this doesn't connect
            self.motor_name = self.context.PV_DICT.get('motor', None)
            print("connecting to: ", self.motor_name)
            self.motor = IMS(self.motor_name, name='jet_x')
        elif not self.live:
            self.motor = SimulatedMotor(self.context, self.signals)
            pass

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
        # ["resume", "everything is good", "you downgraded", "you upgraded", "pause", "missed shots", "high intensity"]
        print(info)
        if info == "everything is good":
            # if this info is passed then the status was changed from missed shots to everything is good
            if len(self.moves) > 0:
                self.good_edge_points.append(self.moves[-1])
        if info == "resume":
            # if this info is passed then the status was changed from dropped shots and the motor should resume
            self.pause = False
        if info == "you downgraded":
            # this is when the status is changed from high intensity to missed shots
            pass
        if info == "you upgraded":
            # this is when the status is changed from missed shots to high intensity
            pass
        if info == "pause":
            # if this info is passed then the status was changed to dropped shots and the motor should pause
            self.pause = True
        if info == "missed shots":
            # this is when the status changes from everything is good to missed shots
            if len(self.moves) > 0:
                self.bad_edge_points.append(self.moves[-1])
        if info == "high intensity":
            # this is when the status changes from everything is good to high intensity
            self.sweet_spot.append(self.moves[-1])

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
        self.intensities += [self.vals['ratio']]
# this is where we set the integration time for each motor position in the scan
        if len(self.intensities) == 20:
            self.check_motor_options()
            print(self.moves)
            self.moves.append([mean(self.intensities), self.motor.position])  # this should be the same either way
            self.intensities = []
            # for live or sim motor
            if not self.pause:
                self.done, self.max_value = self.action.execute()

    def run(self):
        self.connect_to_motor()
        self.clear_values()
        while not self.isInterruptionRequested():
            if self.done:
                if len(self.moves) > 4:
                    x = [a[1] for a in self.moves]
                    y = [b[0] for b in self.moves]
                    self.signals.plotMotorMoves.emit(self.motor.position, self.max_value, x, y)
                    print("go to sleep now..")
                    time.sleep(7)
                    self.signals.message.emit(f"Found peak intensity {self.max_value} "
                                              f"at motor position: {self.motor.position}")
                    self.signals.sleepMotor.emit()
            else:
                if self.request_new_values and self.got_new_values:
                    self.request_new_values = False
                    self.got_new_values = False
                if not self.request_new_values:
                    self.signals.valuesRequest.emit()
                    self.request_new_values = True
            time.sleep(1/self.refresh_rate)
        print("Interruption was requested: Motor Thread")


"""
        if self.motor_options['scanning algorithm'] == "search":
            while not done:
                self.motor_position = self.motor.position
                self.motor_position, self.ratio_intensity = self._search(self.motor_position, -.01, .01, .0005, 60)
            fig = plt.figure()
            plt.xlabel('motor position')
            plt.ylabel('I/I0 intensity')
            plt.plot(self.motor_position, self.ratio_intensity, 'ro')
            x = [a[0] for a in self.moves]
            y = [b[1] for b in self.moves]
            plt.scatter(x, y)
            plt.show()
            self.signals.update_calibration.emit('ratio', self.ratio_intensity)
            self.signals.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
        elif self.motor_options['scanning algorithm'] == "scan":
            print("scanning :", self.tol, self.motor_ll, self.motor_hl)
            self.motor_position = self._scan(self.motor_ll, self.motor_hl, self.tol, self.motor_options['averaging'])
            self.ratio_intensity = self.moves[-1][1]
            fig = plt.figure()
            plt.xlabel('motor position')
            plt.ylabel('I/I0 intensity')
            plt.plot(self.motor_position, self.ratio_intensity, 'ro')
            x = [a[0] for a in self.moves]
            y = [b[1] for b in self.moves]
            plt.scatter(x, y)
            plt.show()
            self.signals.update_calibration.emit('ratio', self.ratio_intensity)
            self.signals.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
        elif self.move_type == "track": ### these should be inside of each of the scanning algorithms? need to check if were moving once or "Tracking"
            self.signals.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
            #### look up how to exit safely here
        elif self.move_type == "stop tracking":
            self.signals.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
            #### again, exit safely  
"""        
