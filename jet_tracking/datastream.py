import logging
import os
import time
import threading
import json
from pathlib import Path
from statistics import mean, stdev, StatisticsError
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
        print(f"got error [e]")
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
        self.signals = signals
        self.live_data = True
        self.signals.run_live.connect(self.run_live_data)

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
        context_data = zmq.Context()
        socket_data = context_data.socket(zmq.SUB)
        socket_data.connect(''.join(['tcp://localhost:', '8123']))
        socket_data.subscribe("")
        #while True:
        md = socket_data.recv_json(flags=0)
        msg = socket_data.recv(flags=0, copy=False, track=False)
        buf = memoryview(msg)
        data = np.frombuffer(buf, dtype=md['dtype'])
        data = np.ndarray.tolist(data.reshape(md['shape']))
        self.gatt = data[0]
        self.diff = data[1]
	
        #x = 0.8
        #y = 0.4
        #self.gatt = sinwv(x)
        #self.diff = sinwv(y)

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
        self.signals = signals
        self.reader = ValueReader(signals)
        self.status = True
        self.mode = "running"  #can either be running or calibrating
        self.timer = time.time()
        self.buffer_size = 300
        self.count = 0
        self.calibrated = False
        self.calibration_time = 10
        self.calibration_values = {"i0": {'mean': 0, 'stdev': 0}, "diff": {'mean': 0, 'stdev': 0}, "ratio": {'mean': 0, 'stdev': 0}}
        self.nsamp = 50
        self.sigma = 2
        self.samprate = 50
        self.notification_tolerance = 200
        self.i0_rdbutton_selection = 'gatt'

        ## buffers and data collection 
        self.averages = {"average i0":collections.deque([0]*self.buffer_size, self.buffer_size), 
                         "average diff": collections.deque([0]*self.buffer_size, self.buffer_size),
                         "average ratio": collections.deque([0]*self.buffer_size, self.buffer_size),
                         "time": collections.deque([0]*self.buffer_size, self.buffer_size)}
        self.flaggedEvents = {"low intensity": collections.deque([0]*self.buffer_size, self.buffer_size),
                            "missed shot": collections.deque([0]*self.buffer_size, self.buffer_size),
                            "dropped shot": collections.deque([0]*self.buffer_size, self.buffer_size)}
        self.buffers = {"i0":collections.deque([0]*self.buffer_size, self.buffer_size),
                        "diff":collections.deque([0]*self.buffer_size, self.buffer_size), 
                        "ratio": collections.deque([0]*self.buffer_size, self.buffer_size), 
                        "time": collections.deque([0]*self.buffer_size, self.buffer_size)}
        
        ## signals
        self.signals.rdbttn_status.connect(self.update_rdbutton)
        self.signals.nsampval.connect(self.update_nsamp)
        self.signals.sigmaval.connect(self.update_sigma)
        self.signals.samprate.connect(self.update_samprate)
        self.signals.mode.connect(self.update_mode)
        self.signals.motormove.connect(self.motor_interface)
        self.signals.update_calibration.connect(self.update_cali)

    def update_mode(self, mode):
        self.mode = mode

    def update_cali(self, name, val):
        self.calibration_values[name] = val
        self.signals.calibration_value.emit(self.calibration_values)

    def update_status(self, status):
        self.status = status
    
    def update_sigma(self, sigma):
        self.sigma = sigma
        print(self.sigma)

    def update_nsamp(self, nsamp):
        self.nsamp = nsamp
        print(self.nsamp)
        
    def update_samprate(self, samprate):
        self.samprate = samprate
        
    def update_rdbutton(self, rdbutton):
        self.i0_rdbutton_selection = rdbutton

    def run(self):
        """Long-running task."""

        while not self.isInterruptionRequested():
            new_values = self.reader.read_value() 
            if self.mode == "running":
                if self.count < self.buffer_size:
                    self.count += 1
                    self.buffers['i0'].append(new_values.get(self.i0_rdbutton_selection))
                    self.buffers['diff'].append(new_values.get('diff'))
                    self.buffers['ratio'].append(new_values.get('ratio'))
                    self.buffers['time'].append(time.time()-self.timer) ### time should be the clock time instead of runtime
                else: 
                    self.count += 1 #### do I need to protect from this number getting too big?
                    self.buffers['i0'].append(new_values.get(self.i0_rdbutton_selection))
                    self.buffers['diff'].append(new_values.get('diff'))
                    self.buffers['ratio'].append(new_values.get('ratio'))
                    self.buffers['time'].append(time.time()-self.timer)
                    self.event_flagging()
                if self.count % self.nsamp == 0:
                    try:
                        avei0 =  mean(Skimmer('dropped shot',
                                           list(self.buffers['i0']), self.flaggedEvents))
                        self.averages["average i0"].append(avei0)
                        avediff =  mean(Skimmer('dropped shot',
                                           list(self.buffers['diff']), self.flaggedEvents))
                        self.averages["average diff"].append(avediff)
                        averatio =  mean(Skimmer('dropped shot',
                                     list(self.buffers['ratio']), self.flaggedEvents))
                        self.averages["average ratio"].append(averatio)
                    except StatisticsError:
                        for i in range(len(self.averages)-1):
                            keys = [*self.averages.keys()]
                            self.averages[keys[i]].append(0)
                            #self.signals.message.emit("You are having a hard time getting averages, likely due to too much flagging. Try changing sigma.")
                    self.averages["time"].append(time.time()-self.timer)
                    self.signals.avevalues.emit(self.averages)
                    self.check_status_update()
                self.signals.buffers.emit(self.buffers)
                time.sleep(1/self.samprate)
            elif self.mode == "calibration":
                print("calibrating...")
                self.calibrate(new_values)
            elif self.mode == "get calibration":
                self.get_calibration_vals() 

    def check_status_update(self):

        if self.calibrated:
            if np.count_nonzero(self.flaggedEvents['missed shot']) > self.notification_tolerance:
                self.signals.status.emit("warning, missed shots", "red") # a way to clock how long it's in a warning state before it needs recalibration
            elif np.count_nonzero(self.flaggedEvents['dropped shot'])> self.notification_tolerance:
                self.signals.status.emit("lots of dropped shots", "yellow")
            elif np.count_nonzero(self.flaggedEvents['low intensity']) > self.notification_tolerance:
                self.signals.status.emit("low intensity", "orange")
            else:
                self.signals.status.emit("everything is good", "green")
        else:
            self.signals.status.emit("not calibrated", "orange")

    def event_flagging(self):
        ###  better way to do this??
        if (self.buffers['ratio'][-1] <  
                (self.calibration_values['ratio']['mean'] - 
                self.sigma*self.calibration_values['ratio']['stdev'])):
            self.flaggedEvents['low intensity'].append(self.buffers['ratio'][-1])
        else:
            self.flaggedEvents['low intensity'].append(0)
        if (self.buffers['i0'][-1] < 
                (self.calibration_values['i0']['mean'] - 
                self.sigma*self.calibration_values['i0']['stdev'])):
            self.flaggedEvents['dropped shot'].append(self.buffers['i0'][-1])
        else:
            self.flaggedEvents['dropped shot'].append(0)
        if (self.buffers['ratio'][-1] < 
                (self.calibration_values['ratio']['mean'] - 
                2*self.sigma*self.calibration_values['ratio']['stdev'])):
            #print(self.buffers['ratio'][-1], self.calibration_values['ratio']['mean'] - 
            #    2*self.sigma*self.calibration_values['ratio']['stdev'])
            self.flaggedEvents['missed shot'].append(self.buffers['i0'][-1])
        else:
            self.flaggedEvents['missed shot'].append(0)

    def get_calibration_vals(self):
        results, cal_file = get_cal_results('xcs', 'xcsx47519') ### change the experiment
        if results == None:
            self.signals.message.emit("no calibration file there")
            pass
        self.calibration_values['i0']['mean'] =  float(results['i0_median'])
        self.calibration_values['i0']['stdev'] = float(results['i0_low'])
        self.calibration_values['ratio']['mean'] = float(results['mean_ratio'])
        self.calibration_values['ratio']['stdev'] = float(results['std_ratio'])
        self.signals.calibration_value.emit(self.calibration_values)
        self.calibrated = True
        self.mode = 'running'
        self.signals.message.emit(str(cal_file))
        self.signals.message.emit("i0 median: " + results['i0_median'])
        self.signals.message.emit( 'i0 low: ' + results['i0_low'])
        self.signals.message.emit('mean ratio: ' + results['mean_ratio'])
        self.signals.message.emit('standard deviation of the ratio: ' + (results['std_ratio']))
        self.signals.calibration_value.emit(self.calibration_values)
    
    def calibrate(self, v):
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
                time.sleep(1/self.samprate)
        self.calibration_values['i0']['mean'] = mean(cal_values[0])
        self.calibration_values['i0']['stdev'] = stdev(cal_values[0])
        self.calibration_values['diff']['mean'] = mean(cal_values[1])
        self.calibration_values['diff']['stdev'] = stdev(cal_values[1])
        self.calibration_values['ratio']['mean'] = mean(cal_values[2])
        self.calibration_values['ratio']['stdev'] = stdev(cal_values[2])
        """
        cal_values = [[], [], []] 
        while time.time()-timer < 3:#self.calibration_time: # put a time limit on how long it can try to calibrate for before throwing an error - set status to no tracking
            if (v.get(self.i0_rdbutton_selection) >= 
                    (self.calibration_values['i0']['mean'] - 
                    2*self.calibration_values['i0']['stdev'])):
                cal_values[0].append(v.get(self.i0_rdbutton_selection))
            if (v.get('diff') >= 
                    (self.calibration_values['diff']['mean'] - 
                    2*self.calibration_values['diff']['stdev'])):
                cal_values[1].append(v.get('diff'))
            if (v.get('ratio') >= 
                    (self.calibration_values['ratio']['mean'] - 
                    2*self.calibration_values['ratio']['stdev'])):
                cal_values[2].append(v.get('ratio'))
            time.sleep(1/2)
        self.calibration_values['i0']['mean'] = mean(cal_values[0])
        self.calibration_values['i0']['stdev'] = stdev(cal_values[0])
        self.calibration_values['diff']['mean'] = mean(cal_values[1])
        self.calibration_values['diff']['stdev'] = stdev(cal_values[1])
        self.calibration_values['ratio']['mean'] = mean(cal_values[2])
        self.calibration_values['ratio']['stdev'] = stdev(cal_values[2])
        """
        self.calibrated = True
        self.mode = "running"
        self.signals.calibration_value.emit(self.calibration_values)
 
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
        self.signals = signals
        self.nsamp = 10
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

        self.signals.limits.connect(self.get_limits)
        self.signals.tol.connect(self.get_tol)
        # self.signals.nsamp.connect(self.get_nsamp) 

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
            #m1 = self.motor_ll + (self.motor_hl-self.motor_ll)/3
            #m2 = self.motor_hl - (self.motor_hl-self.motor_hl)/3
            self.motor_position = self._search(self.motor_hl, self.motor_ll, self.tol, 100)
            self.ratio_intensity = self.ratio.get()
            fig = plt.figure()
            plt.xlabel('motor position')
            plt.ylabel('I/I0 intensity')
            plt.plot(self.motor_position, self.ratio_intensity, 'ro')
            x = [a[0] for a in self.moves]
            y = [b[0] for b in self.moves]
            plt.scatter(x, y)
            plt.show()
            self.signals.update_calibration.emit('ratio', self.ratio_intensity)
            self.signals.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
        elif self.move_type == "scan":
            print("scanning :", self.tol, self.motor_ll, self.motor_hl)
            self.motor_position = self._scan(self.motor_ll, self.motor_hl, self.tol, self.nsamp)
            self.ratio_intensity = self.ratio.get()
            fig = plt.figure()
            plt.xlabel('motor position')
            plt.ylabel('I/I0 intensity')
            plt.plot(self.motor_position, self.ratio_intensity, 'ro')
            x = [a[0] for a in self.moves]
            y = [b[0] for b in self.moves]
            plt.scatter(x, y)
            plt.show()
            self.signals.update_calibration.emit('ratio', self.ratio_intensity)
            self.signals.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
        elif self.move_type == "track":
            self.signals.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
            #### look up how to exit safely here
        elif self.move_type == "stop tracking":
            self.signals.finished.emit({'position': self.motor_position, 'ratio': self.ratio_intensity})
            #### again, exit safely  

    def average_int(self, nsamp):
       i0 = []
       for i in range(nsamp):
          i0.append(self.ratio.get())
          time.sleep(1/50)
       return(mean(i0))

    def _search(self, left, right, tol, nsamp):
        if abs(right - left) < tol:
            self.motor.move((left+right)/2)
            return((left+right)/2)
        left_third = (2*left + right) / 3
        right_third = (left + 2*right) / 3
        self.motor.move(left_third, wait=True)
        left = self.motor.position
        i1 = self.average_int(nsamp)
        self.motor.move(right_third, wait=True)
        right = self.motor.position        
        i2 = self.average_int(nsamp)
        self.moves.extend([(left, i1), (right, i2)])

        if i1 < i2:
            return(self._search(left_third, right, tol/2))
        else:
            return(self._search(right_third, left, tol/2)) 


    def _scan(self, left, right, tol, nsamp):
        # scans in positive direction in steps of tol
        # until the intensity starts going down
        i1 = self.average_int(nsamp)
        m1 = self.motor.position
        self.motor.move(tol, wait=True)
        i2 = self.average_int(nsamp)
        m2 = self.motor.position
        self.moves.extend([(m1, i1), (m2, i2)])
        if i1 < i2: #shot 1 is i1 and shot 2 is i2
            while i1 < i2:
                print("i1<i2", i1, i2)
                i1 = self.average_int(nsamp)
                self.position_left = self.motor.position
                self.motor.move(tol, wait=True)
                i2 = self.average_int(nsamp)
                self.position_right = self.motor.position
                self.moves.extend([(m2, i2)])
                print(self.moves)
            # this is for graphing purposes to prove that the peak was found
            # it should be commented out after full testing
            i = 0
            for i in range(5):
                i+=1
                self.motor.move(tol, wait=True)
                self.moves.append([(self.motor.position, self.average_int(nsamp))])
            self.motor.move(self.position_left, wait=True)
            return(self.position_left)

        else: #go back and move right
            # makes a large step to the negative position
            # ideally such that it goes OVER the peak
            # 
            self.motor.move(left, wait=True)
            i1 = self.average_int(nsamp)
            m1 = self.motor.position
            self.motor.move(tol, wait=True)
            i2 = self.average_int(nsamp)
            m2 = self.motor.position
            self.moves.extend([(m1, i1), (m2, i2)])
            print(i1, i2)
            if i1 < i2:
                while i1 < i2:
                    i1 = self.average_int(nsamp)
                    self.position_left = self.motor.position
                    self.motor.move(tol, wait=True)
                    i2 = self.average_int(nsamp)
                    self.position_right = self.motor.position
                    self.moves.extend([(m2, i2)])
                    print(self.moves)
                i = 0
                for i in range(5):
                    i+=1
                    self.motor.move(tol, wait=True)
                    self.moves.append([(self.motor.position, self.average_int(nsamp))])
                self.motor.move(self.position_left, wait=True)
                return(self.position_left)
         
             
#class MotorEdit(QUndoCommand):
#    def __init__(self, motor, position):
#       super(MotorEdit, self).__init__()
#       self.motor = motor
#       self.position = position
#
#    def redo(self):
#       self.motor.mo

