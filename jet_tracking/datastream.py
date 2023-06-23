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
from scipy import stats
from motorMoving import MotorAction
from tools.numGen import SimulationGenerator
from tools.simMotorMoving import SimulatedMotor
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
                    cls._instances[cls] = super().__call__(
                        *args, **kwargs)
        return cls._instances[cls]


class ValueReader(metaclass=Singleton):
    """
    Singleton class for reading and providing values.

    Attributes:
        signals (Signals): The signals object for emitting signals.
        context (Context): The context object for accessing context information.
        live_data (bool): Flag indicating whether live data is enabled.
        live_initialized (bool): Flag indicating if live data is initialized.
        connected (bool): Flag indicating if connections are made.
        signal_diff (EpicsSignal): The EpicsSignal object for diff signal.
        signal_i0 (EpicsSignal): The EpicsSignal object for i0 signal.
        signal_ratio (EpicsSignal): The EpicsSignal object for ratio signal.
        signal_dropped (EpicsSignal): The EpicsSignal object for dropped signal.
        simgen (SimulationGenerator): The SimulationGenerator object for simulation data generation.
        sim_vals (dict): Dictionary containing simulation values.
        diff (float): The diff value.
        i0 (float): The i0 value.
        ratio (float): The ratio value.
        dropped (bool): Flag indicating if data is dropped.
    """
    def __init__(self, context, signals):
        """
        Initialize the ValueReader.

        Args:
            context (Context): The context object for accessing context information.
            signals (Signals): The signals object for emitting signals.
        """
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
        """
        Make connections for the ValueReader.
        """
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
            except Exception as e:
                self.live_initialized = False
                self.connected = False
                self.signals.message.emit(f"Could not connect to the PVs for the data stream, {type(e).__name__}")
            else:
                self.live_initialized = False
                self.connected = False
                self.signals.message.emit("Could not connect to the PVs for the data stream")
        elif not self.live_data:
            self.simgen = SimulationGenerator(self.context, self.signals)
            self.connected = True

    def run_live_data(self, live):
        """
        Set the flag for live data.

        Args:
            live (bool): Flag indicating whether live data is enabled.
        """
        self.live_data = live
        if self.connected:
            self.connected = False

    def live_data_stream(self):
        """
        Stream live data and update values.
        """
        if not self.live_initialized:
            # should not ever get here
            self.signals.message.emit("The live data"
                                      "stream is not working")
        self.i0 = self.signal_i0.get()
        self.diff = self.signal_diff.get()
        self.ratio = self.signal_ratio.get()

    def sim_data_stream(self):
        """
        Stream simulation data and update values.
        """
        self.sim_vals = self.simgen.sim()
        self.i0 = self.sim_vals["i0"]
        self.diff = self.sim_vals["diff"]
        self.ratio = self.sim_vals["ratio"]
        self.dropped = self.sim_vals["dropped"]

    def read_value(self):
        """
        Read the current value.

        Returns:
            dict: Dictionary containing the current values.
        """
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
        Initialize the StatusThread.

        This method initializes the StatusThread object with the given context and signals.
        It sets various attributes and initializes data buffers and dictionaries.

        Parameters:
        ----------
        context : object
            The context object containing configuration settings.
        signals : object
            The signals object used for inter-thread communication.

        Attributes:
        ----------
        signals : object
            The signals object that contains different signals for communication.
        context : object
            The context object that contains various settings and parameters.
        mode : str
            The current mode of the status thread.
        paused : bool
            Indicates whether the status thread is paused or not.
        calibration_source : str
            The source of calibration values (either 'calibration from results' or 'calibration in GUI').
        calibration_priority : str
            The priority of the calibration process.
        num_cali : int
            The number of calibration points.
        refresh_rate : float
            The refresh rate for the data collection.
        percent : int
            The percentage for the calibration range.
        num_points : int
            The number of data points to display.
        graph_ave_time : int
            The averaging time for the graph display.
        naverage : int
            The number of points to average for the calculations.
        averaging_size : int
            The size of the averaging buffer.
        notification_tolerance : int
            The tolerance for triggering notifications.
        x_axis : int
            The x-axis value.
        bad_scan_limit : int
            The limit for the number of bad scans.
        flag_message : None
            Placeholder for the flag message.
        display_time : int
            The display time for the graph.
        _count : int
            The current count for the x-axis index.
        _ave_count : int
            The current count for the averaging.
        calibrated : bool
            Indicates whether the status thread is calibrated or not.
        isTracking : bool
            Indicates whether the status thread is tracking or not.
        bad_scan_counter : int
            The counter for bad scans.
        status : str
            The current status of the status thread.
        display_flag : list
            The display flag list.
        cal_vals : list
            The calibration values list.
        averages : dict
            The dictionary of average values.
        flagged_events : dict
            The dictionary of flagged events.
        current_values : dict
            The dictionary of current values.
        buffers : dict
            The dictionary of buffers.
        calibration_values : dict
            The dictionary of calibration values.
        reader : ValueReader
            The ValueReader object for reading values.
        processor_worker : EventProcessor
            The EventProcessor object for processing events.
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
        """
        Connect signals to corresponding slots.

        This method connects various signals to their corresponding slots in the StatusThread object.
        """
        self.signals.changeStatusMode.connect(self.update_mode)
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

    def set_new_axis(self, idx):
        """
        Set a new x-axis for the graph.

        This method sets a new x-axis for the graph based on the provided the index value of first nan.

        Parameters:
        ----------
        idx : int
            The current index of first nan value
        """
        self.display_time = self.context.display_time
        self.refresh_rate = self.context.refresh_rate
        self.num_points = self.display_time * self.refresh_rate
        self._count = idx

    def start_com(self):
        """
        Start the communication process.

        This method starts the communication process by running a continuous loop that processes events and runs the data thread.
        """
        while not self.thread().isInterruptionRequested():
            QCoreApplication.processEvents(QEventLoop.AllEvents,
                                           int(self.refresh_rate*1000))
            self.run_data_thread()

    def start_it(self):
        """
        Start the StatusThread.

        This method starts the StatusThread by setting the paused attribute to False.
        """
        log.info("Inside of the start_it method of StatusThread.")
        self.paused = False

    def stop_it(self, abort):
        """
        Stop the StatusThread.

        This method stops the StatusThread by setting the paused attribute to True. If abort is True, the thread will be interrupted.

        Parameters:
        ----------
        abort : bool
            A flag indicating whether the thread should be interrupted.
        """
        self.paused = True
        if abort:
            self.thread().requestInterruption()
        else:
            pass

    def run_data_thread(self):
        """
        Run the data thread.

        This method is the long-running task that collects data points. It reads values from the ValueReader,
        updates buffers, checks status updates, calculates averages, and emits signals to refresh graphs.

        Note: This method runs in a continuous loop until the thread is paused.
        """
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

    def tracking(self, b):
        """
        Set the tracking mode.

        This method sets the tracking mode based on the provided boolean value.

        Parameters:
        ----------
        b : bool
            A flag indicating whether tracking mode should be enabled.
        """
        self.isTracking = b
        print(self.isTracking)

    def update_mode(self, mode):
        """
        Update the mode.

        This method updates the mode attribute of the StatusThread object with the provided mode.

        Parameters:
        ----------
        mode : str
            The new mode value.
        """
        log.info("Inside of the update_mode method of StatusThread.")
        self.mode = mode

    def set_percent(self, p):
        """
        Set the percent value.

        This method sets the percent attribute of the StatusThread object with the provided value.

        Parameters:
        ----------
        p : int
            The new percent value.
        """
        self.percent = p
        self.update_calibration_range()

    def set_calibration_source(self, c):
        """
        Set the calibration source.

        This method sets the calibration_source attribute of the StatusThread object with the provided value.

        Parameters:
        ----------
        c : object
            The new calibration source value.
        """
        self.calibration_source = c
    
    def set_num_cali(self, n):
        """
        Set the number of calibration.

        This method sets the num_cali attribute of the StatusThread object with the provided value.

        Parameters:
        ----------
        n : int
            The new number of calibration value.
        """
        self.num_cali = n

    def set_calibration_priority(self, p):
        """
        Set the calibration priority.

        This method sets the calibration_priority attribute of the StatusThread object with the provided value.
        This can either be 'recalibrate' or 'keep calibration'

        Parameters:
        ----------
        p : object
            The new calibration priority value.
        """
        self.calibration_priority = p

    def set_scan_limit(self, sl):
        """
        Set the scan limit.

        Parameters:
        sl (int): The scan limit value.
        """
        self.bad_scan_limit = sl

    def calculate_averages(self):
        """
        Calculate the averages of the buffer values and update the averages dictionary.
        """
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
        Add values from the ValueReader to the buffers dictionary and check if the events should be flagged.

        Parameters:
        vals (dict): The values received from the ValueReader.
        """
        v = [vals.get('diff'), vals.get('i0'),
             vals.get('ratio'), vals.get('dropped')]
        if self.calibrated:
            self.event_flagging(v)
        for k in self.buffers.keys():
            self.buffers[k].append(vals.get(k))

    def check_status_update(self):
        """
        Check the status update based on the flagged events and emit signals accordingly.
        """
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
                self.processor_worker.count_flags_and_execute('missed shot', 20,
                                                   self.missed_shots)
            elif n_drop > self.notification_tolerance:
                self.signals.changeStatus.emit("Lots of dropped shots",
                                               "yellow")
                self.processor_worker.count_flags_and_execute('dropped shot', 20,
                                                   self.dropped_shots)
            elif n_high > self.notification_tolerance:
                self.signals.changeStatus.emit("High Intensity", "orange")
                self.processor_worker.count_flags_and_execute('high intensity', 20,
                                                   self.high_intensity)
            else:
                if not self.processor_worker.isCounting:
                    self.signals.changeStatus.emit("Everything is good",
                                                   "green")
                    self.everything_is_good()
                if self.processor_worker.isCounting:
                    self.processor_worker.count_flags_and_execute("everything is good",
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
            Values from the ValueReader in the order i0, diff, ratio
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
        """
        Update the calibration range for the 'i0', 'diff', and 'ratio' signals.

        Calculates the calibration range based on the percent, standard deviation, and mean
        values stored in the calibration_values dictionary. Updates the calibration_values
        dictionary with the new range values. Emits a signal to notify the change in calibration_values.
        """
        for name in ['i0', 'diff', 'ratio']:
            self.calibration_values[name]['range'] = self.normal_range(
                self.percent, self.calibration_values[name]['stddev'],
                self.calibration_values[name]['mean'])
        self.signals.changeCalibrationValues.emit(self.calibration_values)

    def set_calibration_values(self, name, vmean, std):
        """
        Set the calibration values for a given signal name.

        Updates the mean, standard deviation, and range values in the calibration_values dictionary
        for the specified signal name. Also emits signals to notify the change in calibration_values
        and update the calibration display. Additionally, sets the calibration values in the context
        and emits a signal to notify the change in calibration display.

        Args:
            name (str): The name of the signal.
            vmean (float): The mean value for the calibration.
            std (float): The standard deviation value for the calibration.
        """
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

        Args:
            v (dict): A dictionary containing calibration values.
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
        """
        Send intensities information to the motor.

        Emits a signal with the current_values to send intensities information to the motor.
        """
        self.signals.intensitiesForMotor.emit(self.current_values)

    def recalibrate(self):
        """
        Recalibrate the system based on the calibration priority.

        If the calibration priority is set to "keep calibration", emits a message signal stating
        that the calibration will not change. If the priority is set to "recalibrate", updates
        the mode to 'calibrate' by calling the update_mode method.
        """
        if self.calibration_priority == "keep calibration":
            self.signals.message.emit("Calibration will not change. "
                                      "If you would like it to override this, "
                                      "select \"calibrate in gui\" and hit the "
                                      "calibrate button")
        elif self.calibration_priority == "recalibrate":
            self.update_mode("calibrate")

    def missed_shots(self):
        """
        Handle the case of missed shots.

        Checks the motor status and tracking status to determine the appropriate action when
        shots are missed. If the motor is running and the status is 'everything is good', emits
        a notifyMotor signal for missed shots. If the motor is not running and tracking is enabled,
        checks the bad_scan_counter and disables tracking if the limit is reached. If the motor is
        not running and tracking is disabled, emits a message signal suggesting running a search.
        """
        print("processor worker called missed shots.. ", self.isTracking, self.context.motor_connected, self.context.motor_mode)
        if self.context.motor_connected:
            if self.status == "everything is good":
                self.signals.notifyMotor.emit("missed shots")
            elif self.status == "dropped shots":
                self.signals.notifyMotor.emit("resume")
            elif self.status == "high intensity":
                self.signals.notifyMotor.emit("you downgraded")
        if self.isTracking and self.context.motor_mode == "sleep":
            print("tracking and not motor running")
            if self.bad_scan_counter < self.bad_scan_limit:
                print(self.bad_scan_counter, self.bad_scan_limit)
                self.signals.message.emit("lots of missed shots.. "
                                          "starting motor")
                self.context.update_motor_mode("run")
                self.bad_scan_counter += 1
            else:
                self.signals.enableTracking.emit(False)
                self.signals.trackingStatus.emit('disabled', "red")
        elif not self.isTracking and self.context.motor_mode == "sleep":
            self.signals.message.emit("lots of missed shots.. consider running"
                                      " a search")
        self.status = "missed_shots"

    def dropped_shots(self):
        """
        Handle the case of dropped shots.

        Pauses the motor and emits a message signal indicating a high number of dropped shots.
        """
        print("processor worker called dropped shots.. ", self.isTracking, self.context.motor_connected,
              self.context.motor_mode)
        if self.context.motor_connected:
            self.signals.message.emit("lots of dropped shots.. pausing motor")
            self.signals.notifyMotor.emit("pause")
        self.status = "dropped shots"

    def high_intensity(self):
        """
        Handle the case of high intensity.

        Resets the bad_scan_counter and emits appropriate notifyMotor signals based on the current
        status. Sets the status to 'high intensity'.
        """
        print("processor worker called high intensity.. ", self.isTracking, self.context.motor_connected,
              self.context.motor_mode)
        self.bad_scan_counter = 0
        if self.context.motor_connected:
            if self.status == "dropped shots":
                self.notifyMotor("resume")
            elif self.status == "missed shots":
                self.signals.notifyMotor.emit("high intensity")
            elif self.status == "everything is good":
                self.signals.notifyMotor.emit("you upgraded")
        self.status = "high intensity"

    def everything_is_good(self):
        """
        Handle the case when everything is good.

        Resets the bad_scan_counter and stops the processor_worker. Emits appropriate notifyMotor
        signals based on the current status. Sets the status to 'everything is good'.
        """
        print("processor worker called everything is good.. ", self.isTracking, self.context.motor_connected,
              self.context.motor_mode)
        self.bad_scan_counter = 0
        self.processor_worker.stop_count()
        if self.context.motor_connected:
            if self.status == "dropped shots":
                self.signals.notifyMotor("resume")
            elif self.status == "missed shots":
                self.signals.notifyMotor.emit("Everything is good")
            elif self.status == "high intensity":
                self.signals.notifyMotor.emit("you downgraded")
        self.status = "everything is good"


class EventProcessor(QThread):
    """
    A class for processing events and counting flags.

    Inherits from QThread to allow for multi-threading. Handles flag counting and execution
    of associated functions based on the flags.

    Attributes:
        signals (QObject): The signals object for emitting signals.
        flag_type (dict): A dictionary to store the count of different flags.
        isCounting (bool): A flag indicating whether the processor is currently counting.

    Methods:
        count_flags_and_execute(new_flag, num_flagged, func_to_execute):
            Count the occurrence of flags and execute a function when a specific flag count is reached.
        stop_count():
            Stop the flag counting by resetting the flag_type dictionary and isCounting flag.
    """
    def __init__(self, signals):
        """
        Initialize the EventProcessor instance.

        Args:
            signals (object): The signals object for emitting signals.
        """
        super().__init__()
        self.signals = signals
        self.flag_type = {}
        self.isCounting = False

    def count_flags_and_execute(self, new_flag, num_flagged, func_to_execute):
        """
        Count the occurrence of flags and execute a function when a specific flag count is reached.

        Updates the flag_type dictionary with the count of each flag occurrence. When the count
        of a specific flag reaches the num_flagged value, executes the provided func_to_execute
        function. If a flag is encountered multiple times, its count is incremented. If a flag
        count reaches zero, it is removed from the dictionary.

        Args:
            new_flag (any): The new flag value to be counted.
            num_flagged (int): The number of times the new_flag must occur for the function execution.
            func_to_execute (function): The function to be executed when the flag count reaches num_flagged.
        """
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
        """
        Stop the flag counting by resetting the flag_type dictionary and isCounting flag.
        """
        self.flag_type = {}
        self.isCounting = False


class JetImageFeed(QObject):
    """
    Class for managing and processing image feed from a jet camera.

    Inherits from QObject.
    """
    def init_after_move(self, context, signals):
        """
        Initialize the JetImageFeed after a motor move.

        Args:
            context: The context object containing various settings and values.
            signals (QObject): The signals object for emitting and receiving signals.
        """
        self.signals = signals
        self.context = context
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
        self.refresh_rate = self.context.cam_refresh_rate
        self.counter = 0
        self.upper_left = ()
        self.lower_right = ()
        self.calibration_running = False
        self.find_com_bool = False
        self.connected = False
        self.paused = True
        self.request_for_calibration = False
        self.connect_signals()

    def connect_signals(self):
        """
        Connect the signals for image processing, image search, and more.
        """
        self.signals.imageProcessing.connect(self.update_editor_vals)
        self.signals.imageProcessingRequest.connect(self.new_request)
        self.signals.imageSearch.connect(self.start_algorithm)
        self.signals.initializeCamValues.connect(self.update_cam_vals)
        self.signals.startImageThread.connect(self.start_it)
        self.signals.stopImageThread.connect(self.stop_it)
        self.signals.comDetection.connect(self.set_com_on)
        self.signals.linesInfo.connect(self.set_line_positions)
        
    def set_line_positions(self, ul, lr):
        """
        Set the upper left and lower right line positions.

        Args:
            ul (tuple): The upper left position coordinates.
            lr (tuple): The lower right position coordinates.
        """
        self.upper_left = ul
        self.lower_right = lr

    def set_com_on(self):
        """
        Set the find_com_bool flag.
        """
        self.find_com_bool = self.context.find_com_bool
        
    def start_comm(self):
        """
        Start the communication process for image feed processing.
        """
        while not self.thread().isInterruptionRequested():
            QCoreApplication.processEvents(QEventLoop.AllEvents,
                                           int(self.refresh_rate*1000))
            self.run_image_thread()
            
    def start_it(self):
        """
        Start the image processing thread.
        """
        log.info("Inside of the start_it method of StatusThread.")
        self.paused = False

    def stop_it(self, abort):
        """
        Stop the image processing thread.

        Args:
            abort (bool): Whether to abort the thread or not.
        """
        self.paused = True
        if abort:
            self.thread().requestInterruption()
        else:
            pass
    
    def start_algorithm(self):
        """
        Start the image processing algorithm.
        """
        if not self.connected:
            self.connect_cam()
            self.start_it()
            self.signals.message.emit("Cam was not connected yet, try "
                                      "running the algorithm again")
        if self.connected and not self.calibrated:
            if self.paused:
                self.start_it()
            self.context.update_motor_mode("calibrate")
            self.signals.message.emit("The moves were not calibrated yet. "
                                      "Running that first, otherwise the "
                                      "the algorithm will not run properly. "
                                      "Try running it again when this finishes")
        if self.connected and self.calibrated:
            if self.paused:
                self.start_it()
            self.context.update_motor_mode("run")

    def new_request(self, request):
        """
        Set the new request for image processing information to update calibration positions.

        Args:
            request: The new request for image processing.

        Returns:
            None
        """
        self.request_for_calibration = request

    def update_cam_vals(self):
        """
        Update the left threshold value based on the context threshold value.
        """
        self.left_threshold = self.context.threshold

    def connect_cam(self):
        """
        Connect to the camera and update the necessary variables.
        """
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
            if (self.array_size_x_data != self.array_size_x_viewer or
                    self.array_size_y_data != self.array_size_y_viewer):
                self.signals.message.emit("ROI defined with markers in canViewer "
                                          "won't make sense because of different "
                                          "resolutions between the camera and "
                                          "camViewer")
            image = caget(self.cam_name + ':IMAGE1:ArrayData')
            if len(image) == 0:
                self.signals.message.emit("Can't read camera...")
                self.connected = False
            else:
                self.connected = True
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
        """
        Update the editor values based on the provided dictionary.

        Args:
            e: A dictionary containing the image morphology values.
        """
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
        """
        Apply various image editing operations to the input image.

        Args:
            im: The input image to be edited.

        Returns:
            The edited image after applying the specified operations.
        """
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
            im = cv2.GaussianBlur(im, (3, 3), self.blur, self.blur)
        ret, im = cv2.threshold(im, self.left_threshold, self.right_threshold,
                                cv2.THRESH_BINARY)
        return im
    
    def find_center(self, im):
        """
        Find the center of a jet in the given image.

        Args:
            im: The input image.
        """
        self.locate_jet(im, int(self.upper_left[0]), int(self.lower_right[0]), 
                        int(self.upper_left[1]), int(self.lower_right[1]))
        if self.counter != 20:
            self.counter += 1
        elif self.counter == 20:
            self.counter = 0
            success = self.form_line(self.context.com, int(self.upper_left[1]), 
                                     int(self.lower_right[1]))
            self.context.com = []
            if success and self.request_for_calibration:
                self.context.image_calibration_position(self.context.best_fit_line)
                self.signals.imageProcessingComplete.emit(True)
            elif not success and self.request_for_calibration:
                self.signals.imageProcessingComplete.emit(False)
            self.request_for_calibration = False

    def locate_jet(self, im, x_start, x_end, y_start, y_end):
        """
        Locate the jet in the specified region of interest (ROI) in the image.

        Args:
            im: The input image.
            x_start: The starting x-coordinate of the ROI.
            x_end: The ending x-coordinate of the ROI.
            y_start: The starting y-coordinate of the ROI.
            y_end: The ending y-coordinate of the ROI.
        """
        crop = im[y_start:y_end, x_start:x_end]
        crop = cv2.convertScaleAbs(crop)
        self.context.contours, hierarchy = cv2.findContours(crop, cv2.RETR_EXTERNAL,
                                                    cv2.CHAIN_APPROX_SIMPLE, 
                                                    offset=(x_start, y_start)) 
        if len(self.context.contours) == 0:
            self.signals.message.emit("Was not able to find any contours. \n"
                                      "Try changing the ROI or image editing "
                                      "parameters")
        else:
            contours = [] # Did I intend to leave out the first contours detected above?
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            empty = False
            while not empty:
                crop = cv2.erode(crop, kernel, iterations=1)
                c, h = cv2.findContours(crop, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE,
                                        offset=(x_start, y_start))
                for cont in c:
                    contours.append(cont)
                if len(c) == 0:
                    empty = True
            self.context.com += self.find_com(contours)
            return

    @staticmethod
    def find_com(contours):
        """
        Find the center of mass (COM) for each contour.

        Args:
            contours: A list of contours.

        Returns:
            A list of center of mass (COM) coordinates.
        """
        centers = []
        for i in range(len(contours)):
            M = cv2.moments(contours[i])
            if M['m00'] != 0:
                centers.append((int(M['m10']/M['m00']), int(M['m01']/M['m00'])))
        return centers

    def form_line(self, com, y_min, y_max):
        """
        Form a line using the center of mass (COM) coordinates.

        Args:
            com: A list of center of mass (COM) coordinates.
            y_min: The minimum y-value for the line.
            y_max: The maximum y-value for the line.

        Returns:
            True if the line is successfully formed, False otherwise.
        """
        xypoints = list(zip(*com))
        y = np.asarray(list(xypoints[0]))
        x = np.asarray(list(xypoints[1]))
        res = stats.linregress(x, y)
        # for 95% confidence
        slope = res.slope
        intercept = res.intercept
        confidence_interval = 95
        pvalue = res.pvalue  # if p-value is > .1 get another image and try again
        slope_err = res.stderr
        intercept_err = res.intercept_stderr
        alpha = 1 - (confidence_interval / 100)
        critical_prob = 1 - alpha/2
        degrees_of_freedom = len(com) - 2
        tinv = lambda p, df: abs(stats.t.ppf(p/2., df))
        ts = tinv(alpha, degrees_of_freedom)
        y = np.append(y, [y_min, y_max])
        if slope:
            x_model = (y - intercept)*(1/slope)
            x_model_plus = (y - intercept - ts*intercept_err)*(1 / (slope + ts*slope_err))
            x_model_minus = (y - intercept + ts * intercept_err) * (1 / (slope - ts * slope_err))
            yl = list(y)
            i_max = yl.index(max(yl))
            i_min = yl.index(min(yl))
            self.context.best_fit_line = [[int(yl[i_min]), int(x_model[i_min])],
                                  [int(yl[i_max]), int(x_model[i_max])]]
            self.context.best_fit_line_plus = [[int(yl[i_min]), int(x_model_plus[i_min])],
                                       [int(yl[i_max]), int(x_model_plus[i_max])]]
            self.context.best_fit_line_minus = [[int(yl[i_min]), int(x_model_minus[i_min])],
                                        [int(yl[i_max]), int(x_model_minus[i_max])]]
            return True
        else:
            return False

    def run_image_thread(self):
        """
        Run the image processing thread.

        This function processes the image if the thread is not paused and the camera is connected.
        If live data is available, it retrieves the image from the camera. Otherwise, it generates
        a simulated image. The image is then processed using the editor function. If the
        find_com_bool flag is set, the center of the jet is located in the image. Finally, the
        processed image is emitted through the camImager signal.
        """
        if not self.paused:
            if self.connected:
                if self.context.live_data:
                    image_array = caget(self.cam_name + ':IMAGE1:ArrayData')
                    image = np.reshape(image_array, (self.array_size_y_viewer,
                                           self.array_size_x_viewer))
                else:
                    self.cam_name.gen_image()
                    image = self.cam_name.jet_im
                image = self.editor(image)
                if self.find_com_bool:
                    self.find_center(image)
                self.signals.camImager.emit(image)
        time.sleep(1/self.refresh_rate)


class MotorThread(QObject):
    """
    Represents a thread for motor control and calibration.

    This class handles motor control and calibration operations. It receives signals
    and performs the corresponding actions based on the signal received. It maintains
    various state variables to keep track of motor settings, calibration parameters,
    and communication status.

    Attributes:
        algorithm (str): The algorithm to use for motor control.
        low_limit (float): The lower limit of the motor position.
        high_limit (float): The upper limit of the motor position.
        step_size (float): The step size for motor movement.
        tolerance (float): The tolerance for motor position accuracy.
        calibration_values (dict): The calibration values for motor calibration.
        calibration_priority (str): The priority for motor calibration.
        refresh_rate (int): The refresh rate for motor control operations.
        moves (list): List of motor moves performed.
        intensities (list): List of intensities for motor calibration.
        calibration_steps (int): Number of calibration steps.
        calibration_tries (int): Number of calibration tries.
        vals (dict): Dictionary to store various motor values.
        done (bool): Flag indicating if motor calibration is done.
        motor_name (str): The name of the motor.
        motor (object): The motor object.
        live (bool): Flag indicating if the motor is in live mode.
        connected (bool): Flag indicating if the motor is connected.
        wait (bool): Flag indicating if the motor should wait.
        mode (str): The mode of the motor.
        initial_position (float): The initial position of the motor.
        averaging (int): The number of values to average for motor position.
        request_new_values (bool): Flag indicating if new motor values are requested.
        got_new_values (bool): Flag indicating if new motor values are received.
        request_image_processor (bool): Flag indicating if image processor is requested.
        complete_image_processor (bool): Flag indicating if image processor is complete.
        pix_per_mm (float): Pixels per millimeter for motor calibration.
        good_edge_points (list): List of good edge points for motor calibration.
        bad_edge_points (list): List of bad edge points for motor calibration.
        sweet_spot (list): The sweet spot for motor calibration.
        max_value (float): The maximum value for motor calibration.
        paused (bool): Flag indicating if the motor thread is paused.
        action (object): The MotorAction object for motor actions.
    """
    def init_after_move(self, context, signals):
        """
        Initialize the MotorThread object after moving.

        This method initializes the MotorThread object with the given context and signals.
        It sets up the initial values for various attributes based on the context.

        Args:
            context: The context object containing motor settings and parameters.
            signals: The signals object for communicating with other components.
        """
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
        self.calibration_tries = 0
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
        """
        Establishes signal connections for motor control.

        This method establishes connections between various signals and their corresponding
        slots for motor control and calibration. It connects signals for changing calibration
        priority, updating intensities for motor calibration, connecting to the motor,
        enabling live motor mode, notifying motor, changing motor mode, completing image
        processing, starting the motor thread, and stopping the motor thread.
        """
        self.signals.changeCalibrationPriority.connect(self.set_calibration_priority)
        self.signals.intensitiesForMotor.connect(self.update_values)
        self.signals.connectMotor.connect(self.connect_to_motor)
        self.signals.liveMotor.connect(self.live_motor)
        self.signals.notifyMotor.connect(self.impart_knowledge)
        self.signals.motorMode.connect(self.change_motor_mode)
        self.signals.imageProcessingComplete.connect(self.next_calibration_position)
        self.signals.startMotorThread.connect(self.start_it)
        self.signals.stopMotorThread.connect(self.stop_it)

    def check_motor_options(self):
        """
        Checks and updates motor options from the context.

        This method retrieves and updates motor options such as the algorithm,
        low limit, high limit, step size, calibration values, and refresh rate
        from the context.

        """
        self.algorithm = self.context.algorithm
        self.low_limit = self.context.low_limit
        self.high_limit = self.context.high_limit
        self.step_size = self.context.step_size
        self.calibration_values = self.context.calibration_values
        self.refresh_rate = self.context.refresh_rate

    def start_com(self):
        """
        Starts the communication loop for the motor thread.

        This method starts the communication loop for the motor thread. It runs
        the `run_motor_thread` method in a loop until the thread is interrupted.
        It also processes events to ensure responsiveness.

        """
        log.debug("Inside of the start_com method of MotorThread.")
        while not self.thread().isInterruptionRequested():
            self.run_motor_thread()
            QCoreApplication.processEvents(QEventLoop.AllEvents,
                                           int(self.refresh_rate*1000))

    def start_it(self):
        """
        Starts the motor thread.

        This method starts the motor thread by setting the `paused` attribute
        to False.

        """
        log.debug("Inside of the start_it method of MotorThread.")
        self.paused = False

    def stop_it(self, abort):
        """
        Stops the motor thread.

        This method stops the motor thread by setting the `paused` attribute
        to True. If `abort` is True, it also requests interruption for the thread.
        Otherwise, it emits a message to pause the data stream.

        Args:
            abort (bool): A flag indicating whether to abort the thread.

        """
        self.paused = True
        if abort:
            self.thread().requestInterruption()
        else:
            self.signals.message.emit('Pause Data Stream')

    def set_calibration_priority(self, p):
        """
        Sets the calibration priority.

        This method sets the calibration priority to .

        Args:
            p (str): The calibration priority to set.

        """
        self.calibration_priority = p

    def change_motor_mode(self, m):
        """
        Changes the motor mode.

        This method changes the motor mode. It handles different
        cases based on the current mode and the requested mode.

        Args:
            m (str): The motor mode to change to.

        """
        if not self.connected:
            try:
                self.connect_to_motor()
            except:
                self.mode = "sleep"
        if self.connected:
            if m == 'sleep' and self.mode == 'run':
                self.signals.message.emit('Motor.. go to sleep now..')
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
        """
        Moves the motor to the input position.

        This method moves the motor to the input position `mp`.

        Args:
            mp (float): The target motor position.

        """
        self.motor.move(mp, self.wait)
        self.signals.changeMotorPosition.emit(self.motor.position)

    def live_motor(self, live):
        """
        Sets the motor to live or simulated mode.

        This method sets the motor mode to live or simulated.

        Args:
            live (bool): A flag indicating whether to set the motor to live mode.

        """
        self.live = live
        if self.connected:
            self.connected = False

    def connect_to_motor(self):
        """
        Connects to the motor.

        This method connects to the motor based on whether running live or simulated.
        """
        if self.live:
            self.motor_name = self.context.PV_DICT.get('motor', None)
            self.signals.message.emit("Trying to connect to: "+ self.motor_name)
            try:
                self.motor = Motor(self.motor_name, name='jet_x')
                time.sleep(1)
                # for i in self.motor.component_names: ## this is a good diagnostic
                #    print(f"{i} {getattr(self.motor, i).connected}")
                self.context.update_read_motor_position(self.motor.position)
            except Exception as e:
                self.connected = False
                self.signals.message.emit(f"Could not connect to the PVs for the motor, {type(e).__name__}")
            else:
                self.connected = False
                self.signals.message.emit(f"Could not connect to the PVs for the motor.")
        elif not self.live:
            self.motor = SimulatedMotor(self.context, self.signals)
            self.context.update_motor_position(self.motor.position)
            self.connected = True
            self.wait = False
        if self.connected:
            self.context.motor_connected = True

    def clear_values(self):
        """
        Clears the values of various variables used in the system.

        Resets the following variables:
        - self.moves: List of moves (unclear what type of moves).
        - self.done: Boolean indicating if a task is completed.
        - self.request_new_values: Boolean indicating if new values are requested.
        - self.got_new_values: Boolean indicating if new values have been received.
        - self.request_image_processor: Boolean indicating if image processing is requested.
        - self.complete_image_processor: Boolean indicating if image processing is completed.
        - self.good_edge_points: List of edge points considered "good".
        - self.bad_edge_points: List of edge points considered "bad".
        - self.calibration_steps: Number of calibration steps.
        - self.calibration_tries: Number of calibration attempts.
        - self.sweet_spot: List of positions considered as the "sweet spot".
        - self.max_value: Maximum value (unclear what it represents).
        """
        self.moves = []
        self.done = False
        self.request_new_values = False
        self.got_new_values = False
        self.request_image_processor = False
        self.complete_image_processor = False
        self.good_edge_points = []
        self.bad_edge_points = []
        self.calibration_steps = 1
        self.calibration_tries = 0
        self.sweet_spot = []
        self.max_value = 0

    def impart_knowledge(self, info):
        """
        Handles the imparting of knowledge to the system.

        Args:
        - info (str): Information provided to the system. Possible values are:
          - "resume": Indicates that the system should resume from a paused state.
          - "everything is good": Indicates that everything is in a good state.
          - "you downgraded": Indicates a change from high intensity to missed shots.
          - "you upgraded": Indicates a change from missed shots to high intensity.
          - "pause": Indicates that the system should pause.
          - "missed shots": Indicates a change from everything is good to missed shots.
          - "high intensity": Indicates a change from everything is good to high intensity.
        """
        self.signals.message.emit(info)
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
        """
        Moves the motor to the next calibration position based on the calibration step.

        Args:
        - success (bool): Indicates if the calibration attempt was successful.
        """
        if success:
            if self.calibration_steps == 1:
                self.initial_position = self.motor.position
            if self.calibration_steps >= 6:
                self.motor.move(self.initial_position - (self.step_size*(self.calibration_steps-5)), self.wait)
            else:
                self.motor.move(self.initial_position + (self.step_size * self.calibration_steps), self.wait)
            if not self.live:
                time.sleep((1/self.refresh_rate)*3)
            self.calibration_steps += 1
        else:
            self.calibration_tries += 1
            if self.calibration_tries == 3:
                self.motor.move(self.initial_position, self.wait)
                self.mode = "sleep"
                self.signals.message.emit("Image calibration failed")
        self.context.update_read_motor_position(self.motor.position)
        self.complete_image_processor = True

    def update_image_calibration(self):
        """
        Updates the image calibration values.

        Calculates the pixels per millimeter value based on the image calibration positions.
        """
        pix_per_mm = []
        image_calibration_positions = self.context.image_calibration_positions
        for i in range(len(image_calibration_positions)-1):
            motor_pos_diff = abs(image_calibration_positions[i+1][0] -
                                 image_calibration_positions[i][0])
            image_pos_diff = abs(image_calibration_positions[i+1][1][0][1] -
                                 image_calibration_positions[i][1][0][1])
            pix_per_mm.append(image_pos_diff/motor_pos_diff)
        self.pix_per_mm = mean(pix_per_mm)
        self.signals.message.emit(f"pix per mm: {self.pix_per_mm}")

    def update_values(self, vals):
        """
        Updates the values used in the system.

        Args:
        - vals (dict): Dictionary of updated values.

        The function performs the following actions:
        - Checks if the system is not done.
        - Sets self.got_new_values to True.
        - Calls self.check_motor_options().
        - Updates self.vals and triggers the self.average_intensity() function if the values have changed and 'dropped' is False.
        """
        if not self.done:
            self.got_new_values = True
            self.check_motor_options()
            if vals != self.vals and vals['dropped'] is False:
                self.vals = vals
                self.average_intensity()
            else:
                pass

    def average_intensity(self):
        """
        Calculates and updates the average intensity values.

        Updates the intensities list with the ratio value from self.vals.
        When the intensities list reaches a length of 20, the following actions are performed:
        - Prints the intensities list (for debugging purposes).
        - Calls self.check_motor_options().
        - Prints the moves list (for debugging purposes).
        - Appends a new move to the moves list, consisting of the mean of intensities and the current motor position.
        - Resets the intensities list.
        - If not paused, calls self.action.execute() to determine if the task is completed and updates self.done and self.max_value accordingly.
        """
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
        """
        Runs the motor in a separate thread based on the current mode.

        The function performs different actions depending on the current mode:
        - If the mode is 'run':
            - If the task is done:
                - If the number of moves is greater than 4:
                    - Retrieves the motor positions and intensities from the moves list.
                    - Emits a signal to plot the motor moves.
                    - Pauses for 7 seconds.
                    - Emits a signal with information about the peak intensity and motor position.
                    - Updates the motor position in the context.
                    - Emits a signal to indicate that the motor algorithm has finished.
                - Otherwise:
                    - Updates the motor position in the context.
                    - Emits a signal to indicate that the motor should go to sleep.
                    - Updates the motor mode in the context to 'sleep'.
            - If the task is not done:
                - If a new values request is requested and new values have been received:
                    - Resets the new values request and new values received flags.
                - If a new values request is not requested:
                    - Emits a signal to request new values.
                    - Sets the new values request flag.
        - If the mode is 'calibrate':
            - If the calibration steps reach 11:
                - Moves the motor to the initial position.
                - Updates the read motor position in the context.
                - Pauses for 3 times the inverse of the refresh rate.
                - Emits a signal to request image processing with False parameter.
                - Updates the image calibration based on the captured positions.
                - Clears the image calibration positions list in the context.
                - Resets the calibration steps to 1.
                - Sets the mode to 'sleep'.
                - Updates the motor mode in the context to 'sleep'.
            - If the calibration steps are not 11:
                - If an image processing request is requested and image processing is completed:
                    - Resets the image processing request and image processing completion flags.
                - If an image processing request is not requested:
                    - If not in live mode, pauses for 3 times the inverse of the refresh rate.
                    - Emits a signal to request image processing with True parameter.
                    - Sets the image processing request flag.
        - If the mode is 'sleep':
            - Clears the values of various variables.
        - Pauses for the inverse of the refresh rate.
        """
        if not self.paused:
            if self.mode == 'run':
                if self.done:
                    if len(self.moves) > 4:
                        x = [a[1] for a in self.moves]
                        y = [b[0] for b in self.moves]
                        self.signals.plotMotorMoves.emit(self.motor.position, self.max_value, x, y)
                        time.sleep(7)
                        self.signals.message.emit(f"Found peak intensity {self.max_value} "
                                                  f"at motor position: {self.motor.position}")
                        self.context.update_motor_position(self.motor.position)
                        self.context.update_motor_mode('sleep')
                        self.signals.finishedMotorAlgorithm.emit()
                    else:
                        self.context.update_motor_position(self.motor.position)
                        self.signals.message.emit("Motor.. go to sleep now..")
                        self.context.update_motor_mode('sleep')
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
