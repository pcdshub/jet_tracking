import logging
import time
import threading
from statistics import mean

import numpy as np
import pyqtgraph as pg
import zmq
from ophyd import EpicsSignal
from pydm import Display
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import (QButtonGroup, QComboBox, QLCDNumber, QRadioButton,
                             QTextEdit)
from qtpy import QtCore
from qtpy.QtCore import *
from qtpy.QtWidgets import (QApplication, QFrame, QGraphicsScene,
                            QGraphicsView, QHBoxLayout, QLabel, QPushButton,
                            QVBoxLayout)

from num_gen import *
from calibration import Calibration
from graph_display import graphDisplay
from signals import Signals
import collections

logging = logging.getLogger('ophyd')
logging.setLevel('CRITICAL')

lock = threading.Lock()

def getPVs():
    # this is where I would want to get PVs from a json file
    # but I will hard code it for now
    return({'diff': 'CXI:JTRK:REQ:DIFF_INTENSITY', 'gatt': 'CXI:JTRK:REQ:I0'})


class Counter(QObject):

    def __init__(self, signals, nsamp, parent=None):
        super(QObject, self).__init__(parent)

        self.signals = signals
        self.nsamp = nsamp
        self.bttnstatus = 0
        self.timer = time.time()

        self.signals.rdbttnStatus.connect(self.changeBttn)

    def start(self):

        self.checkBttn()

    def checkBttn(self):

        if self.bttnstatus == 0:
            self.runlive()

        elif self.bttnstatus == 1:
            self.runsim()

    def changeBttn(self, value):

        self.bttnstatus = value
        self.signals.stopped.emit()

    def runlive(self):

        values = [[], [], [], []]

        c = 0

        def diff_cb(value, c):
            if len(self.diff_values) > self.nsamp:
                self.diff_values.pop(0)
            # diff_pv.put(49*0.6*3*np.random.rand()-0.5)
            values[0].append(value)

        def i0_cb(value, c):
            if len(self.i0_values) > self.nsamp:
                self.i0_values.pop(0)
            # i0_pv.put(79+2*np.random.rand())
            values[1].append(value)

        self.diff_values = []
        self.i0_values = []
        c = 0
        PVs = getPVs()
        diff_pv = EpicsSignal(PVs[0])
        i0_pv = EpicsSignal(PVs[1])

        while True:

            cur_time = time.time()-self.timer
            c += 1
            diff_cb(diff_pv.get(), c)
            i0_cb(i0_pv.get(), c)
            values[2].append(cur_time)
            values[3].append(c)
            time.sleep(1/10)
            self.signals.params.emit(values)

        self.signals.stopped.emit()

    def runsim(self):
        
        self.context_data = zmq.Context()
        self.socket_data = self.context_data.socket(zmq.SUB)
        self.socket_data.connect(''.join(['tcp://localhost:', '8123']))
        self.socket_data.subscribe("")

        values = [[], [], [], []]
        c = 0

        while True:
            cur_time = time.time()-self.timer
            c += 1
            md = self.socket_data.recv_json(flags=0)
            msg = self.socket_data.recv(flags=0, copy=False, track=False)
            buf = memoryview(msg)
            data = np.frombuffer(buf, dtype=md['dtype'])
            data = np.ndarray.tolist(data.reshape(md['shape']))
            if len(values[3]) > 120:
                values[3] *= 0  # values[0][-120:]
                # values[1] = values[1][-120:]
                # values[2] = values[2][-120:]
                # values[3] = values[3][-120:]

            values[0].append(data[0])
            values[1].append(data[1])
            values[2].append(cur_time)
            values[3].append(c)

            self.signals.params.emit(values)

        self.signals.stopped.emit()
        
        

def skimmer(key, oldlist, checklist):
    skimlist = []
    for i in range(len(checklist[key])):
        if checklist[key][i] == 0:
            skimlist.append(oldlist[i])
    return(skimlist)

def div_with_try(v1, v2):
    try:
        a = v1/v2
    except (TypeError, ZeroDivisionError) as e:
        a = 0
    return(a)
        

class Singleton(type): #need to make into a singleton
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
        self.PVs = getPVs()
        gatt = self.PVs.get('gatt', None)
        self.signal_gatt = EpicsSignal(gatt)
        #wave8 = self.PVs.get('wave8', None)
        #self.signal_wave8 = EpicsSignal(wave8)
        diff = self.PVs.get('diff', None)
        self.signal_diff = EpicsSignal(diff)
        self.gatt = self.signal_gatt.get()
        self.diff = self.signal_diff.get()

    def sim_data_stream(self):
        """
        context_data = zmq.Context()
        socket_data = context_data.socket(zmq.SUB)
        socket_data.connect(".join(['tcp://localhost:', '8123'])")
        socket_data.subscribe("")
        while True:
            md = socket_data.rev_json(flags=0)
            msg = socket.recv(flags=0,copy=false, track=false)
            buf = memoryview(msg)
            data = np.frombuffer(buf, dtype=md['dtype'])
            data = np.ndarray.tolist(data.reshape(md['shape']))
            self.gatt = data[0]
            self.diff = data[1]
        """
        x = 0.8
        y = 0.4
        self.gatt = sinwv(x)
        self.diff = sinwv(y)

    def read_value(self): # needs to initialize first maybe using a decorator?
        if self.live_data:
            self.live_data_stream()
            return({'gatt': self.gatt, 'diff': self.diff})
        else:
            self.sim_data_stream()
            return({'gatt': self.gatt, 'diff': self.diff})


    #def filter_data():
        # this function is used to remove any keys from the dictionary that have None for the value
        #d = {k, v for k, v in self.signal_dict.items() if v is not None}
        #return
 
class StatusThread(QThread):

    def __init__(self, signals, parent=None):
        super(StatusThread, self).__init__(parent)
        """ Constructor

        :param 
        """
        self.signals = signals
        self.reader = ValueReader(signals)
        self.status = True
        self.mode = "running" #can either be running or calibrating
        self.timer = time.time()
        self.buffer_size = 300
        self.count = 0
        self.calibrated = False
        self.calibration_time = 10
        self.calibration_values = {"i0": 0, "diff":0, "ratio": 0}
        self.nsamp = 10
        self.sigma = 1
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
        self.signals.mode.connect(self.update_mode)

    def update_mode(self, mode):
        self.mode = mode

    def update_status(self, status):
        self.status = status
    
    def update_sigma(self, sigma):
        self.sigma = sigma

    def update_nsamp(self, nsamp):
        self.nsamp = nsamp

    def update_rdbutton(self, rdbutton):
        self.i0_rdbutton_selection = rdbutton

    def run(self):
        """Long-running task."""

        while not self.isInterruptionRequested():
            new_values = self.reader.read_value() #### how does this line work? does it initialize ValueReader first?
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
                    avei0 =  mean(skimmer('dropped shot',
                                           list(self.buffers['i0']), self.flaggedEvents))
                    self.averages["average i0"].append(avei0)
                    avediff =  mean(skimmer('dropped shot',
                                           list(self.buffers['diff']), self.flaggedEvents))
                    self.averages["average diff"].append(avediff)
                    averatio =  mean(skimmer('dropped shot',
                                     list(self.buffers['ratio']), self.flaggedEvents))
                    self.averages["average ratio"].append(averatio)
                    self.averages["time"].append(time.time()-self.timer)
                    self.signals.avevalues.emit(self.averages)
                    self.check_status_update()
                #else:
                #    self.calibrate(new_values)
                self.signals.buffers.emit(self.buffers)
                time.sleep(1/10)
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

        if self.buffers['ratio'][-1] < (self.calibration_values['ratio'] - self.sigma*self.calibration_values['ratio']):
            self.flaggedEvents['low intensity'].append(self.buffers['ratio'][-1])
        else:
            self.flaggedEvents['low intensity'].append(0)
        if self.buffers['i0'][-1] < (self.calibration_values['i0']- self.sigma*self.calibration_values['i0']):
            self.flaggedEvents['dropped shot'].append(self.buffers['i0'][-1])
        else:
            self.flaggedEvents['dropped shot'].append(0)
        if self.buffers['diff'][-1] < (self.calibration_values['diff']- self.sigma*self.calibration_values['diff']):
            self.flaggedEvents['missed shot'].append(self.buffers['i0'][-1])
        else:
            self.flaggedEvents['missed shot'].append(0)
        
    def calibrate(self, v):

        timer = time.time()
        cal_values = [[],[],[]]
        while time.time()-timer < 3:#self.calibration_time: # put a time limit on how long it can try to calibrate for before throwing an error - set status to no tracking
            cal_values[0].append(v.get(self.i0_rdbutton_selection))
            cal_values[1].append(v.get('diff'))
            cal_values[2].append(div_with_try(v.get('diff'), v.get('i0')))
        self.calibration_values['i0'] = mean(cal_values[0])
        self.calibration_values['diff'] = mean(cal_values[1])
        self.calibration_values['ratio'] = mean(cal_values[2])
        self.calibrated = True
        self.mode = "running"
        self.signals.calibration_value.emit(self.calibration_values)
    
                   

class GraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.setMouseTracking(True)


class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(GraphicsScene, self).__init__(parent)


class ComboBox(QComboBox):
    def __init__(self, parent=None):
        super(ComboBox, self).__init__(parent)


class PushButton(QPushButton):
    def __init__(self, parent=None):
        super(PushButton, self).__init__(parent)


class Label(QLabel):
    def __init__(self, parent=None):
        super(Label, self).__init__(parent)

    def setTitleStylesheet(self):
        self.setStyleSheet("\
                qproperty-alignment: AlignCenter;\
                border: 1px solid #FF17365D;\
                border-top-left-radius: 15px;\
                border-top-right-radius: 15px;\
                background-color: #FF17365D;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                max-height: 35px;\
                font-size: 14px;\
            ")

    def setSubtitleStyleSheet(self):
        self.setStyleSheet("\
                qproperty-alignment: AlignCenter;\
                border: 1px solid #FF17365D;\
                background-color: #FF17365D;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                font-size: 12px;\
            ")

    def setTrackingStylesheet(self):
        # this will change based on the status given back
        self.setStyleSheet("\
                qproperty-alignment: AlignCenter;\
                border: 1px solid #FF17365D;\
                background-color: red;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                font-size: 12px;\
            ")


class JetTracking(Display):
    rdbuttonstatus = pyqtSignal(int)
    sigmaval = pyqtSignal(int)
    nsampval = pyqtSignal(int)

    def __init__(self, parent=None, args=None, macros=None):
        super(JetTracking, self).__init__(parent=parent, args=args, macros=macros)

        # reference to PyDMApplication - this line is what makes it so that you
        # #can avoid having to define main() and instead pydm handles that
        # for you - it is a subclass of QWidget
        self.app = QApplication.instance()
        # load data from file
        self.load_data()

        self.signals = Signals()
        self.vreader = ValueReader(self.signals)
        self.worker = StatusThread(self.signals)
        print(self.worker.isRunning())
        self.buffer_size = 300 
        self.correction_thread = None
        # assemble widgets
        self.setup_ui()

    def minimumSizeHint(self):

        return(QtCore.QSize(1000, 600))

    def ui_filepath(self):

        # no Ui file is being used as of now
        return(None)

    def load_data(self):

        # this is responsible for opening the database and adding the information to self.data
        # https://slaclab.github.io/pydm-tutorial/action/python.html

        pass

    def setup_ui(self):
        # set default style sheet
        # self.setDefaultStyleSheet()

        # create layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # give it a title
        self.lbl_title = Label("Jet Tracking")
        self.lbl_title.setTitleStylesheet()
        self._layout.addWidget(self.lbl_title)
        self.lbl_title.setMaximumHeight(35)

        # add a main layout for under the title which holds graphs and user controls
        self.layout_main = QHBoxLayout()
        self._layout.addLayout(self.layout_main)

        #####################################################################
        # make views/scenes to hold pydm graphs
        #####################################################################

        ################################
        # setup layout
        self.frame_graph = QFrame()
        self.frame_graph.setMinimumHeight(500)
        self.layout_graph = QVBoxLayout()
        self.frame_graph.setLayout(self.layout_graph)
        ################################

        # default is to use live graphing
        self.liveGraphing()

        #####################################################################
        # set up user panel layout and give it a title
        #####################################################################
        self.frame_usr_cntrl = QFrame()
        self.frame_usr_cntrl.setMinimumHeight(500)
        self.layout_usr_cntrl = QVBoxLayout()
        self.frame_usr_cntrl.setLayout(self.layout_usr_cntrl)

        self.lbl_usr_cntrl = Label("User Controls")
        self.lbl_usr_cntrl.setTitleStylesheet()
        self.lbl_usr_cntrl.setMaximumHeight(35)
        self.layout_usr_cntrl.addWidget(self.lbl_usr_cntrl)

        #####################################################################
        # make radiobutton for selecting live or simulated data
        #####################################################################

        self.bttngrp1 = QButtonGroup()
        self.rdbttn_live = QRadioButton("live data")  # .setChecked(True)
        self.rdbttn_sim = QRadioButton("simulated data")  # .setChecked(False)
        self.rdbttn_live.setChecked(True)
        self.bttngrp1.addButton(self.rdbttn_live)
        self.bttngrp1.addButton(self.rdbttn_sim)
        self.bttngrp1.setExclusive(True)  # allows only one button to be selected at a time

        self.bttngrp2 = QButtonGroup()
        self.rdbttn_manual = QRadioButton("manual motor moving")  # .setChecked(True)
        self.rdbttn_auto = QRadioButton("automated motor moving")  # .setChecked(False)
        self.rdbttn_manual.setChecked(True)
        self.bttngrp2.addButton(self.rdbttn_manual)
        self.bttngrp2.addButton(self.rdbttn_auto)
        self.bttngrp2.setExclusive(True)  # allows only one button to be selected at a time

        # setup layout
        ##############
        self.frame_rdbttns = QFrame()
        self.layout_allrdbttns = QGridLayout()
        self.frame_rdbttns.setLayout(self.layout_allrdbttns)
        self.layout_usr_cntrl.addWidget(self.frame_rdbttns)
        self.layout_allrdbttns.addWidget(self.rdbttn_live, 0, 0)
        self.layout_allrdbttns.addWidget(self.rdbttn_sim, 0, 1)
        self.layout_allrdbttns.addWidget(self.rdbttn_manual, 1, 0)
        self.layout_allrdbttns.addWidget(self.rdbttn_auto, 1, 1)

        #####################################################################
        # make drop down menu for changing nsampning for sigma
        #####################################################################

        self.lbl_cbox_sigma = Label("Sigma")
        self.lbl_cbox_sigma.setSubtitleStyleSheet()

        self.cbox_sigma = ComboBox()
        self.cbox_sigma.addItems(['1', '1.5', '2', '2.5', '3'])

        self.lbl_tbox_nsamp = Label('number of samples')
        self.lbl_tbox_nsamp.setSubtitleStyleSheet()

        # self.tbox_nsamp = QLineEdit("10")
        # self.validator = QIntValidator(0, 300)
        # self.tbox_nsamp.setValidator(self.validator)
        self.cbox_nsamp = ComboBox()
        self.cbox_nsamp.addItems(['10', '20', '50', '120'])

        # setup layout
        ##############
        self.frame_cbox_sigma = QFrame()
        self.layout_cbox_sigma = QHBoxLayout()
        self.frame_cbox_sigma.setLayout(self.layout_cbox_sigma)
        self.layout_usr_cntrl.addWidget(self.frame_cbox_sigma)
        self.layout_cbox_sigma.addWidget(self.lbl_cbox_sigma)
        self.layout_cbox_sigma.addWidget(self.cbox_sigma)

        self.frame_tbox_nsamp = QFrame()
        self.layout_tbox_nsamp = QHBoxLayout()
        self.frame_tbox_nsamp.setLayout(self.layout_tbox_nsamp)
        self.layout_usr_cntrl.addWidget(self.frame_tbox_nsamp)
        self.layout_tbox_nsamp.addWidget(self.lbl_tbox_nsamp)
        self.layout_tbox_nsamp.addWidget(self.cbox_nsamp)  # self.tbox_nsamp)
        ############################

        ####################################################################
        # make buttons to choose between devices for checking if we have beam
        # currently either gas attenuator in the FEE or the Wave8
        ####################################################################

        self.lbl_init_initensity = Label("Initial beam Intensity RBV")
        self.lbl_init_initensity.setSubtitleStyleSheet()
        self.bttn_attenuator = PushButton("Gas Attenuator")
        self.bttn_wave8 = PushButton("Wave8")

        # setup layout
        ##############
        self.frame_init_initensity = QFrame()
        self.layout_init_initensity = QHBoxLayout()
        self.frame_init_initensity.setLayout(self.layout_init_initensity)
        self.layout_usr_cntrl.addWidget(self.frame_init_initensity)
        self.layout_init_initensity.addWidget(self.lbl_init_initensity)
        self.layout_init_initensity.addWidget(self.bttn_attenuator)
        self.layout_init_initensity.addWidget(self.bttn_wave8)
        ####################

        #####################################################################
        # give a status area that displays values and current tracking
        # reliability based on various readouts
        #####################################################################

        self.lbl_status = Label("Status")
        self.lbl_status.setTitleStylesheet()

        self.lbl_tracking = Label("Tracking")
        self.lbl_tracking.setSubtitleStyleSheet()
        self.lbl_tracking_status = Label("No Tracking")
        self.lbl_tracking_status.setTrackingStylesheet()
        self.lbl_i0 = Label("Initial intensity (I0) RBV")
        self.lbl_i0.setSubtitleStyleSheet()
        self.lbl_i0_status = QLCDNumber(4)

        self.lbl_diff_i0 = Label("Diffraction at detector")
        self.lbl_diff_i0.setSubtitleStyleSheet()
        self.lbl_diff_status = QLCDNumber(4)

        # setup layout
        ##############
        self.layout_usr_cntrl.addWidget(self.lbl_status)

        self.frame_tracking_status = QFrame()
        self.frame_tracking_status.setLayout(QHBoxLayout())
        self.frame_tracking_status.layout().addWidget(self.lbl_tracking)
        self.frame_tracking_status.layout().addWidget(self.lbl_tracking_status)

        self.frame_i0 = QFrame()
        self.frame_i0.setLayout(QHBoxLayout())
        self.frame_i0.layout().addWidget(self.lbl_i0)
        self.frame_i0.layout().addWidget(self.lbl_i0_status)

        self.frame_diff_i0 = QFrame()
        self.frame_diff_i0.setLayout(QHBoxLayout())
        self.frame_diff_i0.layout().addWidget(self.lbl_diff_i0)
        self.frame_diff_i0.layout().addWidget(self.lbl_diff_status)

        self.layout_usr_cntrl.addWidget(self.frame_tracking_status)
        self.layout_usr_cntrl.addWidget(self.frame_i0)
        self.layout_usr_cntrl.addWidget(self.frame_diff_i0)
        ###############################

        ########################################################################
        # text area for giving updates the user can see
        ########################################################################

        self.text_area = QTextEdit("~~~read only information for user~~~")
        self.text_area.setReadOnly(True)

        self.layout_usr_cntrl.addWidget(self.text_area)

        #########################################################################
        # main buttons!!!!
        #########################################################################

        self.bttn_calibrate = QPushButton("Calibrate")
        self.bttn_calibrate.setStyleSheet("\
            background-color: yellow;\
            font-size:12px;\
            ")
        self.bttn_start = QPushButton("Start")
        self.bttn_start.setStyleSheet("\
            background-color: green;\
            font-size:12px;\
            ")
        self.bttn_stop = QPushButton("Stop")
        self.bttn_stop.setStyleSheet("\
            background-color: red;\
            font-size:12px;\
            ")

        # setup layout
        ##############
        self.frame_jjbttns = QFrame()
        self.frame_jjbttns.setLayout(QHBoxLayout())
        self.frame_jjbttns.layout().addWidget(self.bttn_calibrate)
        self.frame_jjbttns.layout().addWidget(self.bttn_start)
        self.frame_jjbttns.layout().addWidget(self.bttn_stop)

        self.layout_usr_cntrl.addWidget(self.frame_jjbttns)
        ##############################

        # add frame widgets to the main layout of the window
        self.layout_main.addWidget(self.frame_graph, 75)
        self.layout_main.addWidget(self.frame_usr_cntrl, 25)

        self.graph_setup()
        

        ###################################################
        # signals and slots
        ###################################################
        
        self.cbox_sigma.activated.connect(self.update_sigma)
        self.cbox_nsamp.activated.connect(self.update_nsamp)
        self.bttngrp1.buttonClicked.connect(self.checkBttn)
        self.bttngrp2.buttonClicked.connect(self.checkBttn)        
 
        self.bttn_start.clicked.connect(self._start)
        self.bttn_stop.clicked.connect(self._stop)
        self.bttn_calibrate.clicked.connect(self._calibrate)
        self.signals.status.connect(self.update_status)
        self.signals.calibration_value.connect(self.update_calibration)


        self.signals.status.connect(self.update_status)
        self.signals.buffers.connect(self.plot_data)
        self.signals.avevalues.connect(self.plot_ave_data)
 
        ###################################################

    def _start(self):
        ## check if thread is running
        ## if it is we don't want to restart it! we might want to change the mode though
        ## if not start the thread
        ## if thread is running start is pressed do nothing
        self.worker.start()

    def _stop(self):
        self.worker.requestInterruption()
        self.worker.wait()

    def _calibrate(self):
        self.signals.mode.emit("calibration")
        self._start()

    def update_calibration(self, cal):
        try:
            self.worker.requestInterruption()
            self.worker.wait()
        except NameError:
            print("tried to end worker when there wasn't one when updating calibration")
        self.lbl_i0_status.display(cal['i0'])
        self.lbl_diff_status.display(cal['diff'])

    def liveGraphing(self):

        self.clearLayout(self.layout_graph)

        self.graph1 = pg.PlotWidget()
        self.graph2 = pg.PlotWidget()
        self.graph3 = pg.PlotWidget()

        self.layout_graph.addWidget(self.graph1)
        self.layout_graph.addWidget(self.graph2)
        self.layout_graph.addWidget(self.graph3)

        self.graph_setup()

    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            widgetToRemove = layout.itemAt(i).widget()
            layout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

    def graph_setup(self):
        styles = {'color':'b','font-size': '20px'}
        self.graph1.setLabels(left="I/I0", bottom="Time")
        self.graph1.setTitle(title="Intensity Ratio")
        self.graph1.plotItem.showGrid(x=True, y=True)
        self.graph2.setLabels(left="I0", bottom=("Time", "s"))
        self.graph2.setTitle(title="Initial Intensity")
        self.graph2.showGrid(x=True, y=True)
        self.graph3.setLabels(left="I", bottom=("Time", "s"))
        self.graph3.setTitle(title="Diffraction Intensity")
        self.graph3.showGrid(x=True, y=True)
        self.plot1 = pg.ScatterPlotItem(pen=pg.mkPen(width=5, color='r'),
                                          size=1)
        self.graph1.addItem(self.plot1)
        self.plot1ave = pg.PlotCurveItem(pen=pg.mkPen(width=1, color='w'),
                                           size=1, style=Qt.DashLine)
        self.graph1.addItem(self.plot1ave)
        self.plot2 = pg.PlotCurveItem(pen=pg.mkPen(width=2, color='b'), size=1)
        self.graph2.addItem(self.plot2)
        self.plot2ave = pg.PlotCurveItem(pen=pg.mkPen(width=1, color='w'),
                                         size=1, style=Qt.DashLine)
        self.graph2.addItem(self.plot2ave)
        
        self.plot3 = pg.PlotCurveItem(pen=pg.mkPen(width=2, color='g'), size=1)
        self.graph3.addItem(self.plot3)
        self.plot3ave = pg.PlotCurveItem(pen=pg.mkPen(width=1, color='w'),
                                         size=1, style=Qt.DashLine)
        self.graph3.addItem(self.plot3ave)

        self.graph2.setXLink(self.graph1)
        self.graph3.setXLink(self.graph1)
 
    def plot_data(self, data):
        self.plot1.setData(list(data['time']), list(data['ratio']))
        self.graph1.setXRange(list(data['time'])[0], list(data['time'])[-1])
        self.plot2.setData(list(data['time']), list(data['i0']))
        self.plot3.setData(list(data['time']), list(data['diff']))
    
    def plot_ave_data(self, data):
        self.plot1ave.setData(list(data['time']), list(data['average ratio']))
        self.plot2ave.setData(list(data['time']), list(data['average i0']))
        self.plot3ave.setData(list(data['time']), list(data['average diff']))

    def update_status(self, status, color):
        self.lbl_tracking_status.setText(status)
        self.lbl_tracking_status.setStyleSheet(f"\
                background-color: {color};")

    def receive_status(self, status):
        if status == 'outside':
           if self.correction_thread is None:
               #avoid issues with fluctuations and multiple corrections
               self.correction_thread = correctionThread()
               self.correction_thread.finished.connect(self.cleanup_correction)
               self.correction_thread.start()
 
    def update_sigma(self, sigma):
        self.signals.sigmaval.emit(sigma)

    def update_nsamp(self, nsamp):
        self.signals.nsampval.emit(nsamp)
   
    def cleanup_correction(self):
       self.signals.correction_thread = None
       self.thread.reset_buffers(value)
    
    def checkBttn(self, button):
        bttn = button.text()
        if bttn == "simulated data":
            self.signals.run_live.emit(0)
        elif bttn == "live data":
            self.signals.run_live.emit(1)
        elif bttn == "manual motor moving":
            self.signals.motormove.emit(0)
        elif bttn == "automatic motor moving":
            self.signals.motormove.emit(1)

    def setDefaultStyleSheet(self):

        # This should be done with a json file

        self.setStyleSheet("\
            Label {\
                qproperty-alignment: AlignCenter;\
                border: 1px solid #FF17365D;\
                border-top-left-radius: 15px;\
                border-top-right-radius: 15px;\
                background-color: #FF17365D;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                max-height: 35px;\
                font-size: 14px;\
            }")



