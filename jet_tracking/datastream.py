import logging
import time
import threading
from statistics import mean, stdev
import numpy as np
from ophyd import EpicsSignal
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from num_gen import sinwv
import collections
import zmq

logging = logging.getLogger('ophyd')
logging.setLevel('CRITICAL')

lock = threading.Lock()

def GetPVs():
    # this is where I would want to get PVs from a json file
    # but I will hard code it for now
    return({'diff': 'CXI:JTRK:REQ:DIFF_INTENSITY', 'gatt': 'CXI:JTRK:REQ:I0'})        


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
        self.PVs = dict()
        self.PV_signals = list()
        self.live_data = True
        
        self.signals.run_live.connect(self.run_live_data)

    def run_live_data(self, live):
        self.live_data = live

    def live_data_stream(self):
        self.PVs = GetPVs()
        gatt = self.PVs.get('gatt', None)
        self.signal_gatt = EpicsSignal(gatt)
        #wave8 = self.PVs.get('wave8', None)
        #self.signal_wave8 = EpicsSignal(wave8)
        diff = self.PVs.get('diff', None)
        self.signal_diff = EpicsSignal(diff)
        self.gatt = self.signal_gatt.get()
        self.diff = self.signal_diff.get()

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
        #time.sleep(0.1)
        #x = 0.8
        #y = 0.4
        #self.gatt = sinwv(x)
        #self.diff = sinwv(y)

    def read_value(self):  # needs to initialize first maybe using a decorator?
        if self.live_data:
            self.live_data_stream()
            return({'gatt': self.gatt, 'diff': self.diff})
        else:
            self.sim_data_stream()
            return({'gatt': self.gatt, 'diff': self.diff})

 
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
        self.sigma = 1
        self.samprate = 50
        self.notification_tolerance = 100
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

    def update_mode(self, mode):
        self.mode = mode

    def update_status(self, status):
        self.status = status
    
    def update_sigma(self, sigma):
        self.sigma = sigma

    def update_nsamp(self, nsamp):
        self.nsamp = nsamp
        
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
                    self.buffers['ratio'].append(self.buffers['i0'][-1]/self.buffers['diff'][-1])
                    self.buffers['time'].append(time.time()-self.timer)
                else: 
                    self.count += 1 #### do I need to protect from this number getting too big?
                    self.buffers['i0'].append(new_values.get(self.i0_rdbutton_selection))
                    self.buffers['diff'].append(new_values.get('diff'))
                    self.buffers['ratio'].append(self.buffers['i0'][-1]/self.buffers['diff'][-1])
                    self.buffers['time'].append(time.time()-self.timer)
                    self.event_flagging()
                if self.count % self.nsamp == 0:
                    avei0 =  mean(Skimmer('dropped shot',
                                           list(self.buffers['i0']), self.flaggedEvents))
                    self.averages["average i0"].append(avei0)
                    avediff =  mean(Skimmer('dropped shot',
                                           list(self.buffers['diff']), self.flaggedEvents))
                    self.averages["average diff"].append(avediff)
                    averatio =  mean(Skimmer('dropped shot',
                                     list(self.buffers['ratio']), self.flaggedEvents))
                    self.averages["average ratio"].append(averatio)
                    self.averages["time"].append(time.time()-self.timer)
                    self.signals.avevalues.emit(self.averages)
                    self.check_status_update()
                self.signals.buffers.emit(self.buffers)
                time.sleep(1/self.samprate)
            elif self.mode == "calibration":
                self.calibrate(new_values)

    def check_status_update(self):

        if self.calibrated:
            if np.count_nonzero(self.flaggedEvents['missed shot']) > self.notification_tolerance:
                self.signals.status.emit("warning, missed shots, realigning in **", "red") # a way to clock how long it's in a warning state before it needs recalibration
            elif np.count_nonzero(self.flaggedEvents['dropped shot'])> self.notification_tolerance:
                self.signals.status.emit("lots of dropped shots", "yellow")
            elif np.count_nonzero(self.flaggedEvents['low intensity']) > self.notification_tolerance:
                self.signals.status.emit("low intensity, realigning in ***", "orange")
            else:
                self.signals.status.emit("everything is good", "green")
        else:
            self.signals.status.emit("not calibrated", "orange")

    def event_flagging(self):

        if self.buffers['ratio'][-1] < (self.calibration_values['ratio']['mean'] - self.sigma*self.calibration_values['ratio']['stdev']):
            self.flaggedEvents['low intensity'].append(self.buffers['ratio'][-1])
        else:
            self.flaggedEvents['low intensity'].append(0)
        if self.buffers['i0'][-1] < (self.calibration_values['i0']['mean'] - self.sigma*self.calibration_values['i0']['stdev']):
            self.flaggedEvents['dropped shot'].append(self.buffers['i0'][-1])
        else:
            self.flaggedEvents['dropped shot'].append(0)
        if self.buffers['diff'][-1] < (self.calibration_values['diff']['mean']- self.sigma*self.calibration_values['diff']['stdev']):
            self.flaggedEvents['missed shot'].append(self.buffers['i0'][-1])
        else:
            self.flaggedEvents['missed shot'].append(0)
        
    def calibrate(self, v):
        for key in self.calibration_values:
            self.calibration_values[key]['mean'] = 0
            self.calibration_values[key]['stdev'] = 0
        timer = time.time()
        cal_values = [[],[],[]]
        while time.time()-timer < 2:
            cal_values[0].append(v.get(self.i0_rdbutton_selection))
            cal_values[1].append(v.get('diff'))
            cal_values[2].append(DivWithTry(v.get('diff'), v.get(self.i0_rdbutton_selection)))
            time.sleep(1/2)
        self.calibration_values['i0']['mean'] = mean(cal_values[0])
        self.calibration_values['i0']['stdev'] = stdev(cal_values[0])
        self.calibration_values['diff']['mean'] = mean(cal_values[1])
        self.calibration_values['diff']['stdev'] = stdev(cal_values[1])
        self.calibration_values['ratio']['mean'] = mean(cal_values[2])
        self.calibration_values['ratio']['stdev'] = stdev(cal_values[2])
        cal_values = [[], [], []] 
        while time.time()-timer < 3:#self.calibration_time: # put a time limit on how long it can try to calibrate for before throwing an error - set status to no tracking
            if v.get(self.i0_rdbutton_selection) >= (self.calibration_values['i0']['mean'] - 2*self.calibration_values['i0']['stdev']):
                cal_values[0].append(v.get(self.i0_rdbutton_selection))
            if v.get('diff') >= (self.calibration_values['diff']['mean'] - 2*self.calibration_values['diff']['stdev']):
                cal_values[1].append(v.get('diff'))
            if DivWithTry(v.get('diff'), v.get(self.i0_rdbutton_selection)) >= (self.calibration_values['ratio']['mean'] - 2*self.calibration_values['ratio']['stdev']):
                cal_values[2].append(DivWithTry(v.get('diff'), v.get(self.i0_rdbutton_selection)))
            time.sleep(1/2)
        self.calibration_values['i0']['mean'] = mean(cal_values[0])
        self.calibration_values['i0']['stdev'] = stdev(cal_values[0])
        self.calibration_values['diff']['mean'] = mean(cal_values[1])
        self.calibration_values['diff']['stdev'] = stdev(cal_values[1])
        self.calibration_values['ratio']['mean'] = mean(cal_values[2])
        self.calibration_values['ratio']['stdev'] = stdev(cal_values[2])
        self.calibrated = True
        self.mode = "running"
        self.signals.calibration_value.emit(self.calibration_values)
 
