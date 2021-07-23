import logging
import os
import time
import threading
import json
from pathlib import Path
from statistics import mean, stdev, StatisticsError
import scipy.stats as st
import numpy as np
from pcdsdevices.epics_motor import IMS
from ophyd import EpicsSignal
from PyQt5.QtCore import QThread, QObject
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from num_gen import sinwv
import collections
import matplotlib.pyplot as plt

logging = logging.getLogger('ophyd')
logging.setLevel('CRITICAL')

lock = threading.Lock()

# constants
JT_LOC = '/cds/group/pcds/epics-dev/espov/jet_tracking/jet_tracking/'
SD_LOC = '/reg/d/psdm/'
PV_DICT = {'diff': 'XCS:JTRK:REQ:DIFF_INTENSITY', 'i0': 'XCS:JTRK:REQ:I0', 'ratio': 'XCS:JTRK:REQ:RATIO'}
CFG_FILE = 'jt_configs/xcs_config.yml'
HUTCH = 'xcs'
EXPERIMENT = 'xcsx1568'


def parse_config(cfg_file=CFG_FILE):
    with open(args.cfg_file) as f:
        yml_dict = yaml.load(f, Loader=yaml.FullLoader)
    return yml_dict
        #api_port = yml_dict['api_msg']['port']
        #det_map = yml_dict['det_map']
        #ipm_name = yml_dict['ipm']['name']
        #ipm_det = yml_dict['ipm']['det']
        #pv_map = yml_dict['pv_map']
        #jet_cam_name = yml_dict['jet_cam']['name']
        #jet_cam_axis = yml_dict['jet_cam']['axis']
        #sim = yml_dict['sim']
        #hutch = yml_dict['hutch']
        #exp = yml_dict['experiment']
        #run = yml_dict['run']

def get_cal_results(hutch, exp):
    results_dir = Path(f'/cds/home/opr/{hutch}opr/experiments/{exp}/jt_calib/')
    cal_files = list(results_dir.glob('jt_cal*'))
    cal_files.sort(key=os.path.getmtime)
    if cal_files:
        cal_file_path = cal_files[-1]
        with open(cal_file_path) as f:
            cal_results = json.load(f)
        return cal_results, cal_file_path
    else:
        return None

def Skimmer(key, oldlist, checklist):
    skimlist = []
    for i in range(len(checklist[key])):
        if checklist[key][i] == 0:
            skimlist.append(oldlist[i])
    return(skimlist)


def DivWithTry(v1, v2):
    try:
        a = v1/v2
    except (TypeError, ZeroDivisionError) as e:
        #print(f"got error [e]")
        a = 0
    return(a)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return(cls._instances[cls])

class ValueReader(metaclass=Singleton):

    def __init__(self, signals):
        self.SIGNALS = signals
        self.live_data = True
        self.SIGNALS.run_live.connect(self.run_live_data)

    def run_live_data(self, live):
        self.live_data = live

    def live_data_stream(self):
        i0 = PV_DICT.get('i0', None)
        self.signal_i0 = EpicsSignal(i0)
        #wave8 = self.PVs.get('wave8', None)
        #self.signal_wave8 = EpicsSignal(wave8)
        diff = PV_DICT.get('diff', None)
        self.signal_diff = EpicsSignal(diff)
        ratio = PV_DICT.get('ratio', None)
        self.signal_ratio = EpicsSignal(ratio)
        self.i0 = self.signal_i0.get()
        self.diff = self.signal_diff.get()
        self.ratio = self.signal_ratio.get()

    def sim_data_stream(self):
        """Run with offline data"""
        #context_data = zmq.Context()
        #socket_data = context_data.socket(zmq.SUB)
        #socket_data.connect(''.join(['tcp://localhost:', '8123']))
        #socket_data.subscribe("")
        #while True:
        #md = socket_data.recv_json(flags=0)
        #msg = socket_data.recv(flags=0, copy=False, track=False)
        #buf = memoryview(msg)
        #data = np.frombuffer(buf, dtype=md['dtype'])
        #data = np.ndarray.tolist(data.reshape(md['shape']))
        #self.i0 = data[0]
        #self.diff = data[1]
	
        x = 0.8
        y = 0.1
        self.i0 = sinwv(x, 5000)
        self.diff = sinwv(y, 2000)
        try:
            self.ratio = self.i0/self.diff
        except:
            self.ratio = self.ratio

    def read_value(self):  # needs to initialize first maybe using a decorator?
        if self.live_data:
            self.live_data_stream()
            return({'i0': self.i0, 'diff': self.diff, 'ratio': self.ratio})
        else:
            self.sim_data_stream()
            return({'i0': self.i0, 'diff': self.diff, 'ratio': self.ratio})

 
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

        parent : optional
        
        """
        self.SIGNALS = signals
        self.context = context
        self.reader = ValueReader(signals)
        self.processor_worker = EventProcessor(signals)
        print("__init__ of StatusThread: %d" % QThread.currentThreadId())
        self.isTracking = False
        self.mode = "running"  #can either be running or calibrating
        self.TIMER = time.time()
        self.BUFFER_SIZE = 300
        self.NOTIFICATION_TOLERANCE = 200
        self.thread_options = {}
        self.count = 0
        self.calibrated = False
        self.cal_vals = [[],[],[]]
        self.calibration_values = {'i0':{'mean':0, 'stdev':0, 'range':(0, 0)}, 'diff':{'mean':0, 'stdev':0, 'range':(0, 0)}, 'ratio':{'mean':0, 'stdev':0, 'range':(0, 0)}}

        ## buffers and data collection 
        self.averages = {"average i0":collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE), 
                         "average diff": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE),
                         "average ratio": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE),
                         "time": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE)}
        self.flagged_events = {"high intensity": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE),
                            "missed shot": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE),
                            "dropped shot": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE)}
        self.buffers = {"i0":collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE),
                        "diff":collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE), 
                        "ratio": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE), 
                        "time": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE)}
        self.dropped_shot_threshold = 1000
        self.flag_message = None

        ## signals
        self.SIGNALS.mode.connect(self.update_mode)
        self.SIGNALS.threadOp.connect(self.set_options)
        self.SIGNALS.enable_tracking.connect(self.tracking)

    def tracking(self, b):
        self.isTracking = b

    def set_options(self, options):
        """sets the thread options anytime something from the main gui side changes
        The thread options are:
        live graphing:
        calibration source
        percent
        averaging
        sampling rate: 
        manual motor: bool
        """
        self.thread_options = options

    def update_mode(self, mode):
        self.mode = mode

    def update_buffer(self, vals):
        if self.count < self.BUFFER_SIZE:
            self.count += 1
            self.buffers['i0'].append(vals.get('i0'))
            self.buffers['diff'].append(vals.get('diff'))
            self.buffers['ratio'].append(vals.get('ratio'))
            self.buffers['time'].append(time.time()-self.TIMER) ### time should be the clock time instead of runtime
        else:
            self.count += 1 #### do I need to protect from this number getting too big?
            self.buffers['i0'].append(vals.get('i0'))
            self.buffers['diff'].append(vals.get('diff'))
            self.buffers['ratio'].append(vals.get('ratio'))
            self.buffers['time'].append(time.time()-self.TIMER)
            self.event_flagging()
        if self.count % self.thread_options['averaging'] == 0:
            try:
                avei0 =  mean(Skimmer('dropped shot',
                                       list(self.buffers['i0']), self.flagged_events))
                self.averages["average i0"].append(avei0)
                avediff =  mean(Skimmer('dropped shot',
                                        list(self.buffers['diff']), self.flagged_events))
                self.averages["average diff"].append(avediff)
                averatio =  mean(Skimmer('dropped shot',
                                         list(self.buffers['ratio']), self.flagged_events))
                self.averages["average ratio"].append(averatio)
            except StatisticsError:
                for i in range(len(self.averages)-1):
                    keys = [*self.averages.keys()]
                    self.averages[keys[i]].append(0)
            self.averages["time"].append(time.time()-self.TIMER)
            self.SIGNALS.avevalues.emit(self.averages)
        self.SIGNALS.buffers.emit(self.buffers)

    def run(self):
        """Long-running task to collect data points"""
        while not self.isInterruptionRequested():
            new_values = self.reader.read_value()
            #print("run method: %d" % QThread.currentThreadId()) 
            if self.mode == "running":
                self.update_buffer(new_values)
                self.check_status_update()
                time.sleep(1/self.thread_options['sampling rate'])
            elif self.mode == "calibrate":
                self.calibrated = False
                self.update_buffer(new_values)
                self.calibrate(new_values)
            elif self.mode == "correcting":
                self.update_buffer(new_values)
        print("Interruption request: %d" % QThread.currentThreadId())

    def check_status_update(self):
        if self.calibrated and self.mode != "correcting":
            #print(self.flagged_events)
            if np.count_nonzero(self.flagged_events['missed shot']) > self.NOTIFICATION_TOLERANCE:
                self.SIGNALS.status.emit("Warning, missed shots", "red")
                self.processor_worker.flag_counter('missed shot', 300, self.wake_motor)
            elif np.count_nonzero(self.flagged_events['dropped shot'])> self.NOTIFICATION_TOLERANCE:
                self.SIGNALS.status.emit("lots of dropped shots", "yellow")
                self.processor_worker.flag_counter('dropped shot',300, self.sleep_motor)
            elif np.count_nonzero(self.flagged_events['high intensity']) > self.NOTIFICATION_TOLERANCE:
                self.SIGNALS.status.emit("High Intensity", "orange") 
                self.processor_worker.flag_counter('high intensity', 1000, self.recalibrate)
            else:
                self.SIGNALS.status.emit("everything is good", "green")
                if self.processor_worker.isCounting == True:
                    self.processor_worker.flag_counter('everything is good', 1000, self.processor_worker.stop_count)
        elif not self.calibrated and self.mode != "correcting":
            self.SIGNALS.status.emit("not calibrated", "orange")
        elif self.mode == "correcting":
            self.SIGNALS.status.emit("Correcting ..", "pink")

    def normal_range(self, percent, sigma, mean):
        """ Used to find the upper and lower values on a normal distribution curve
        Parameters
        ----------
        percent: float
                 the percent represents the range of allowed values from the mean
        sigma: float
                 sigma as provided by the calibration
        mean: float
                 mean as provided by the calibration
        returns
        -------
        a: float
                 the lower value percent/2 away from the mean
        b: float
                 the upper value percent/2 away from the mean
        """
        L = (1. - (percent/100.)) /  2.
        r = 1. - L
        zL = st.norm.ppf(L)
        zr = st.norm.ppf(r)
        a = (zL * sigma) + mean
        b = (zr * sigma) + mean
        return([a, b])

    def event_flagging(self):
        """ The method of flagging values that are outside of the values indicated
        from the gui. Values that fall within the allowed range receive a value of
        zero in self.flagged_events deque. Otherwise, that position gets updated with
        the current value in the buffer.
        """
        if self.buffers['ratio'][-1] > self.calibration_values['ratio']['range'][1]:
            self.flagged_events['high intensity'].append(self.buffers['ratio'][-1])
        else:
            self.flagged_events['high intensity'].append(0)
        if self.buffers['i0'][-1] < self.dropped_shot_threshold:
            self.flagged_events['dropped shot'].append(self.buffers['i0'][-1])
        else:
            self.flagged_events['dropped shot'].append(0)
        if self.buffers['ratio'][-1] < self.calibration_values['ratio']['range'][0]:
            self.flagged_events['missed shot'].append(self.buffers['i0'][-1])
        else:
            self.flagged_events['missed shot'].append(0)

    def get_event(self):
        return(self.flagged_event)

    def set_calibration_values(self, name, mean, std):
        self.calibration_values[name]['mean'] = mean
        self.calibration_values[name]['stdev'] = std
        self.calibration_values[name]['range'] = self.normal_range(self.thread_options['percent'],
                                                                   self.calibration_values[name]['stdev'],
                                                                   self.calibration_values[name]['mean'])
        self.SIGNALS.calibration_value.emit(self.calibration_values)

    def calibrate(self, v):
        """ Either gets the calibration values from the file created by the calibration shared memory process
        or it runs a calibration itself by averaging over a length of time (number of new events) and updates
        the calibration_values dictionary with the mean (or median), standard deviation, and range.
        If the calibration is successful, then the calibration is set to True, mode is set to running,
        and the calibration_values are updated.
        """
        
        if self.thread_options['calibration source'] == "calibration from results":
            results, cal_file = get_cal_results(HUTCH, EXPERIMENT) ### change the experiment
            if results == None:
                self.SIGNALS.message.emit("no calibration file there")
                pass
            self.set_calibration_values('i0', 
                                       float(results['i0_mean']), 
                                       float(results['i0_low'])
                                       )
            self.set_calibration_values('ratio', 
                                       float(results['ratio_median']), 
                                       float(results['ratio_low'])
                                       )
            self.set_calibration_values('diff', 
                                       float(results['diff_mean']), 
                                       float(results['diff_low'])
                                       )
            self.dropped_shot_threshold = self.normal_range(90, 
                                                           self.calibration_values['i0']['stdev'],
                                                           self.calibration_values['i0']['mean']
                                                           )[0]
            self.calibrated = True
            self.mode = 'running'
            self.SIGNALS.message.emit('calibration file: ' + str(cal_file))

        elif self.thread_options['calibration source'] == 'calibration in GUI':
            if v.get('i0') > 500:
                self.cal_vals[0].append(v.get('i0'))
                self.cal_vals[1].append(v.get('diff'))
                self.cal_vals[2].append(v.get('ratio'))
                time.sleep(1/self.thread_options['sampling rate'])
            if len(self.cal_vals[0]) > 100:
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
                self.dropped_shot_threshold = self.normal_range(90, 
                                                               self.calibration_values['i0']['stdev'],
                                                               self.calibration_values['i0']['mean']
                                                               )[0]
                self.calibrated = True
                self.cal_vals = [[],[],[]]
                self.mode = "running"

        else:
            self.SIGNALS.message.emit('was not able to calibrate')
            self.calibrated = False
            self.mode = 'running'
        if self.calibrated:    
            self.SIGNALS.message.emit('i0 median: ' + str(self.calibration_values['i0']['mean']))
            self.SIGNALS.message.emit('i0 low: ' + str(self.calibration_values['i0']['stdev']))
            self.SIGNALS.message.emit('mean ratio: ' + str(self.calibration_values['ratio']['mean']))
            self.SIGNALS.message.emit('standard deviation of the ratio: ' + str(self.calibration_values['ratio']['stdev']))

    def recalibrate(self):
        self.SIGNALS.message.emit("The data may need to be recalibrated. There is consistently higher I/I0 than the calibration..")
 
    def wake_motor(self):
        if self.isTracking:
            self.SIGNALS.message.emit("waking up motor")
            self.SIGNALS.wake.emit()
        else:
            self.SIGNALS.message.emit("consider running a motor search or turning on tracking")

    def sleep_motor(self):
        if self.isTracking:
            self.SIGNALS.message.emit("everything is good.. putting motor to sleep")
            self.SIGNALS.sleep.emit()
        else:
            pass



class EventProcessor(QThread):
    def __init__(self, signals):
        super(EventProcessor, self).__init__()
        self.SIGNALS = signals
        self.flag_type = {}
        self.isCounting = False

    def flag_counter(self, new_flag, num_flagged, func_to_execute):
        self.isCounting = True
        #print("This is inside of the event processor!!!   KSEUHFKJSNFDEKAYWGEFIUHASBDFJYAWEGFUKYHABDFJYAWEGFKHAJWEBD", self.flag_type)
        if new_flag in self.flag_type.copy():
            self.flag_type[new_flag] += 1
            if num_flagged <= self.flag_type[new_flag]:
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


        

class MotorThread(QThread):
    def __init__(self, context, signals):
        super(MotorThread, self).__init__()
        self.SIGNALS = signals
        self.context = context
        self.moves = []
        self.motor_options = {}
        #self.ratio_pv = PV_DICT.get('ratio', None)
        #self.ratio = EpicsSignal(self.ratio_pv)
        #self.ratio_intensity = 0
        #self.motor = IMS('XCS:USR:MMS:39', name='jet_x') # this needs to move out to a cfg file
        #time.sleep(1)
        #for i in self.motor.component_names:
        #    print(i,getattr(self.motor,i).connected)
        #self.motor.log.setLevel(level='CRITICAL')
        self.SIGNALS.motorOp.connect(self.params)

    def params(self, p):
        """ sets the motor options so that it can be used to run the algorithms
        parameters
        ----------
        p: dict
            consists of "high limit", "low limit", "step size", "averaging", and "scanning algorithm"
        """
        self.motor_options = p

    def run(self):
        print("I just want to see when this prints")
        while not self.isInterruptedRequested():
            print("I am now running", self.motor_options)
            time.sleep(3)
            print("I am now going to sleep")
            self.SIGNALS.sleep.emit()
        print("Interruption was requested: ", self.isInterruptedRequested())


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
            self.SIGNALS.update_calibration.emit('ratio', self.ratio_intensity)
            self.SIGNALS.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
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
            self.SIGNALS.update_calibration.emit('ratio', self.ratio_intensity)
            self.SIGNALS.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
        elif self.move_type == "track": ### these should be inside of each of the scanning algorithms? need to check if were moving once or "Tracking"
            self.SIGNALS.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
            #### look up how to exit safely here
        elif self.move_type == "stop tracking":
            self.SIGNALS.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
            #### again, exit safely  
"""        
