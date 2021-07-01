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
from PyQt5.QtCore import QThread
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
PV_DICT = {'diff': 'XCS:JTRK:REQ:DIFF_INTENSITY', 'gatt': 'XCS:JTRK:REQ:I0', 'ratio': 'XCS:JTRK:REQ:RATIO'}
CFG_FILE = 'jt_configs/xcs_config.yml'

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
        gatt = PV_DICT.get('gatt', None)
        self.signal_gatt = EpicsSignal(gatt)
        #wave8 = self.PVs.get('wave8', None)
        #self.signal_wave8 = EpicsSignal(wave8)
        diff = PV_DICT.get('diff', None)
        self.signal_diff = EpicsSignal(diff)
        ratio = PV_DICT.get('ratio', None)
        self.signal_ratio = EpicsSignal(ratio)
        self.gatt = self.signal_gatt.get()
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
        #self.gatt = data[0]
        #self.diff = data[1]
	
        x = 0.8
        y = 0.4
        self.gatt = sinwv(x) + 5000
        self.diff = sinwv(y)
        try:
            self.ratio = self.diff/self.diff
        except:
            self.ratio = self.ratio

    def read_value(self):  # needs to initialize first maybe using a decorator?
        if self.live_data:
            self.live_data_stream()
            return({'gatt': self.gatt, 'diff': self.diff, 'ratio': self.ratio})
        else:
            self.sim_data_stream()
            return({'gatt': self.gatt, 'diff': self.diff, 'ratio': self.ratio})

 
class StatusThread(QThread):

    def __init__(self, signals):
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
        self.reader = ValueReader(signals)
        self.mode = "running"  #can either be running or calibrating
        self.TIMER = time.time()
        self.BUFFER_SIZE = 300
        self.NOTIFICATION_TOLERANCE = 200
        self.thread_options = {}
        self.count = 0
        self.calibrated = False
        self.calibration_time = 10
        self.calibration_values = {'i0':{'mean':0, 'stdev':0, 'range':(0, 0)}, 'diff':{'mean':0, 'stdev':0, 'range':(0, 0)}, 'ratio':{'mean':0, 'stdev':0, 'range':(0, 0)}}
        self.i0_rdbutton_selection = 'gatt' #this should change

        ## buffers and data collection 
        self.averages = {"average i0":collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE), 
                         "average diff": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE),
                         "average ratio": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE),
                         "time": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE)}
        self.flagged_events = {"low intensity": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE),
                            "missed shot": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE),
                            "dropped shot": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE)}
        self.buffers = {"i0":collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE),
                        "diff":collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE), 
                        "ratio": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE), 
                        "time": collections.deque([0]*self.BUFFER_SIZE, self.BUFFER_SIZE)}
        
        ## signals
        self.SIGNALS.mode.connect(self.update_mode)
        self.SIGNALS.motormove.connect(self.motor_interface)
        self.SIGNALS.update_calibration.connect(self.update_cali)

        self.SIGNALS.threadOp.connect(self.set_options)
        # self.init_options() #this needs to only happen if the variables
        # can be set first in the init before the thread is created

    def get_options(self):
        self.SIGNALS.getThreadOptions.emit()

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

    def update_cali(self, name, val):
        self.calibration_values[name] = val
        self.SIGNALS.calibration_value.emit(self.calibration_values)

    def run(self):
        """Long-running task."""

        while not self.isInterruptionRequested():
            new_values = self.reader.read_value() 
            if self.mode == "running":
                if self.count < self.BUFFER_SIZE:
                    self.count += 1
                    self.buffers['i0'].append(new_values.get(self.i0_rdbutton_selection))
                    self.buffers['diff'].append(new_values.get('diff'))
                    self.buffers['ratio'].append(new_values.get('ratio'))
                    self.buffers['time'].append(time.time()-self.TIMER) ### time should be the clock time instead of runtime
                else: 
                    self.count += 1 #### do I need to protect from this number getting too big?
                    self.buffers['i0'].append(new_values.get(self.i0_rdbutton_selection))
                    self.buffers['diff'].append(new_values.get('diff'))
                    self.buffers['ratio'].append(new_values.get('ratio'))
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
                            #self.SIGNALS.message.emit("You are having a hard time getting averages, likely due to too much flagging. Try changing sigma.")
                    self.averages["time"].append(time.time()-self.TIMER)
                    self.SIGNALS.avevalues.emit(self.averages)
                    self.check_status_update()
                self.SIGNALS.buffers.emit(self.buffers)
                time.sleep(1/self.thread_options['sampling rate'])
            elif self.mode == "calibrate":
                self.calibrate(new_values)

    def check_status_update(self):
        if self.calibrated:
            if np.count_nonzero(self.flagged_events['missed shot']) > self.NOTIFICATION_TOLERANCE:
                self.SIGNALS.status.emit("warning, missed shots", "red")
            elif np.count_nonzero(self.flagged_events['dropped shot'])> self.NOTIFICATION_TOLERANCE:
                self.SIGNALS.status.emit("lots of dropped shots", "yellow")
            elif np.count_nonzero(self.flagged_events['high intensity']) > self.NOTIFICATION_TOLERANCE:
                self.SIGNALS.status.emit("High Intensity", "orange") # when timer reaches 2 minutes emit "High intensity still, consider re-calibrating"
            else:
                self.SIGNALS.status.emit("everything is good", "green")
        else:
            self.SIGNALS.status.emit("not calibrated", "orange")

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
                 the upper value percent2 away from the mean
        """
        L = (1 - percent) /  2.
        r = 1 - L
        zL = st.norm.ppf(L)
        zr = st.norm.ppf(r)
        a = (zL * sigma)
        b = (zr * sigma)
        return(a, b)

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
        if self.buffers['i0'][-1] < self.calibration_values['i0']['range'][0]:
            self.flagged_events['dropped shot'].append(self.buffers['i0'][-1])
        else:
            self.flagged_events['dropped shot'].append(0)
        if self.buffers['ratio'][-1] < self.calibration_values['ratio']['range'][0]:
            self.flagged_events['missed shot'].append(self.buffers['i0'][-1])
        else:
            self.flagged_events['missed shot'].append(0)

    def calibrate(self, v):
        if self.thread_options['calibration source'] == "calibration from results":
            results, cal_file = get_cal_results('xcs', 'xcsx47519') ### change the experiment
            if results == None:
                self.SIGNALS.message.emit("no calibration file there")
                pass
            self.calibration_values['i0']['mean'] =  float(results['i0_median'])
            self.calibration_values['i0']['stdev'] = float(results['i0_low'])
            self.calibration_values['i0']['range'] = self.normal_range(self.thread_options['percent'],
                                                                       self.calibration_values['i0']['stdev'],
                                                                       self.calibration_values['i0']['mean'])
            self.calibration_values['ratio']['mean'] = float(results['mean_ratio'])
            self.calibration_values['ratio']['stdev'] = float(results['std_ratio'])
            self.calibration_values['ratio']['range'] = self.normal_range(self.thread_options['percent'],
                                                                       self.calibration_values['ratio']['stdev'],
                                                                       self.calibration_values['ratio']['mean'])
            self.SIGNALS.calibration_value.emit(self.calibration_values)
            self.calibrated = True
            self.mode = 'running'
            self.SIGNALS.message.emit(str(cal_file))
            self.SIGNALS.message.emit('i0 median: ' + results['i0_median'])
            self.SIGNALS.message.emit('i0 low: ' + results['i0_low'])
            self.SIGNALS.message.emit('mean ratio: ' + results['mean_ratio'])
            self.SIGNALS.message.emit('standard deviation of the ratio: ' + (results['std_ratio']))
            self.SIGNALS.calibration_value.emit(results)
        elif self.thread_options['calibration source'] == 'calibration in GUI':
            for key in self.calibration_values:
                self.calibration_values[key]['mean'] = 0
                self.calibration_values[key]['stdev'] = 0
            timer = time.time()
            cal_values = [[],[],[]]
            while time.time()-timer < 5:
                if v.get(self.i0_rdbutton_selection) > 5000:
                    cal_values[0].append(v.get(self.i0_rdbutton_selection))
                    cal_values[1].append(v.get('diff'))
                    cal_values[2].append(v.get('ratio'))
                    time.sleep(1/self.thread_options['sampling rate'])
            self.calibration_values['i0']['mean'] = mean(cal_values[0])
            self.calibration_values['i0']['stdev'] = stdev(cal_values[0])
            self.calibration_values['i0']['range'] = self.normal_range(self.thread_options['percent'],
                                                                       self.calibration_values['i0']['stdev'],
                                                                       self.calibration_values['i0']['mean'])
            self.calibration_values['diff']['mean'] = mean(cal_values[1])
            self.calibration_values['diff']['stdev'] = stdev(cal_values[1])
            self.calibration_values['diff']['range'] = self.normal_range(self.thread_options['percent'],
                                                                         self.calibration_values['diff']['stdev'],
                                                                         self.calibration_values['diff']['mean'])
            self.calibration_values['ratio']['mean'] = mean(cal_values[2])
            self.calibration_values['ratio']['stdev'] = stdev(cal_values[2])
            self.calibration_values['ratio']['range'] = self.normal_range(self.thread_options['percent'],
                                                                          self.calibration_values['ratio']['stdev'],
                                                                          self.calibration_values['ratio']['mean'])
            self.calibrated = True
            self.mode = "running"
            self.SIGNALS.calibration_value.emit(self.calibration_values)
        else:
            self.SIGNALS.message.emit('was not able to calibrate')
            self.calibrated = False
            self.mode = 'running'
 
    def motor_interface(self, val):
        if val == 0:
            # scan
            print("scanning..")
        if val == 1:
            print("tracking..")
            # tracking
        if val == 2:
            print("stop tracking..")
            # stop tracking

class MotorThread(QThread):
    def __init__(self, signals, move_type):
        super(MotorThread, self).__init__()
        self.move_type = move_type
        self.moves = []
        self.SIGNALS = signals
        self.thread_options['averaging'] = 10
        self.motor_position = 0
        self.backlash_step = 0.050
        self.tol = 0.002
        self.motor_ll = -0.02
        self.motor_hl = 0.02
        self.ratio_pv = PV_DICT.get('ratio', None)
        self.ratio = EpicsSignal(self.ratio_pv)
        self.ratio_intensity = 0
        self.motor = IMS('XCS:USR:MMS:39', name='jet_x')
        time.sleep(1)
        for i in self.motor.component_names:
            print(i,getattr(self.motor,i).connected)
        self.motor.log.setLevel(level='CRITICAL')
        self.set_motor_params()

        self.SIGNALS.limits.connect(self.get_limits)
        self.SIGNALS.tol.connect(self.get_tol) 

    def get_limits(self, low, high):
        self.motor_ll = low
        self.motor_hl = high
        print(low, high)

    def get_tol(self, tol):
        self.tol = tol
        print(tol)

    def set_motor_params(self):
        #self.motor_ll = self.motor.low_limit
        #self.motor_hl =self.motor.high_limit
        self.motor_position = self.motor.position

    def run(self):
        if self.move_type == "search":
            self.motor_position = self.motor.position
            self.motor_position, self.ratio_intensity = self._search(self.motor_position, -.01, .01, .0005, 60)
            fig = plt.figure()
            plt.xlabel('motor position')
            plt.ylabel('I/I0 intensity')
            plt.plot(self.motor_position, self.ratio_intensity, 'ro')
            x = [a[0] for a in self.moves]
            y = [b[1] for b in self.moves]
            print(self.moves, x, y)
            plt.scatter(x, y)
            plt.show()
            self.SIGNALS.update_calibration.emit('ratio', self.ratio_intensity)
            self.SIGNALS.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
        elif self.move_type == "scan":
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
        elif self.move_type == "track":
            self.SIGNALS.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
            #### look up how to exit safely here
        elif self.move_type == "stop tracking":
            self.SIGNALS.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
            #### again, exit safely  
        
             
#class MotorEdit(QUndoCommand):
#    def __init__(self, motor, position):
#       super(MotorEdit, self).__init__()
#       self.motor = motor
#       self.position = position
#
#    def redo(self):
#       self.motor.mo

