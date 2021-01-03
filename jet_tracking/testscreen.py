import logging
import time

import numpy as np
import pyqtgraph as pg
import zmq
from ophyd import EpicsSignal
from pydm import Display
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import (QButtonGroup, QComboBox, QLCDNumber, QRadioButton,
                             QTextEdit)
from qtpy import QtCore
from qtpy.QtCore import QThread
from qtpy.QtWidgets import (QApplication, QFrame, QGraphicsScene,
                            QGraphicsView, QHBoxLayout, QLabel, QPushButton,
                            QVBoxLayout)

from calibration import Calibration
from graph_display import graphDisplay
from signals import Signals
import collections

logging = logging.getLogger('ophyd')
logging.setLevel('CRITICAL')

def getPVs():
    # this is where I would want to get PVs from a json file
    # but I will hard code it for now
    return({'diffraction': 'CXI:JTRK:REQ:DIFF_INTENSITY', 'gatt': 'CXI:JTRK:REQ:I0'])


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


class ValueReader(object):
    def __init__(self):

        self.PVs = dict()
        self.PV_signals = list()
        self.live_data = True
        self.epics_signals()

    def epics_signals(self):
        ### Question: how to account for possible missing PVs in json
        ### where all should I be checking for things like none values
        ### how do I notify the user without breaking the whole program
        ### if they try switching to wave8 or something while it's already running

        self.PVs = getPVs()
        gatt = self.PVs.get('gatt', None)
        self.signal_gatt = EpicsSignal(gatt)
        wave8 = self.PVs.get('wave8', None)
        self.signal_wave8 = EpicsSignal(wave8)
        diff = self.PVs.get('diffraction', None)
        self.signal_diff = EpicsSignal(diff)
        
        #p = [gatt, wave8, diff]
        #self.PV_signals = [EpicsSignal(i) for i in p if i is not None]

    def read_value(self):
        if self.live_data:
            return({'gatt': self.signal_gatt.get(), 'wave8': self.signal_wave8.get(), 'diffraction': self.signal_diff.get()}

    #def filter_data():
        # this function is used to remove any keys from the dictionary that have None for the value
        #d = {k, v for k, v in self.signal_dict.items() if v is not None}
        #return
 
class StatusThread(QThread):
    def __init__(self, signals, parent=None):
        super(StatusThread, self).__init__(parent)
        self.signals = signals
        self.mode = None
        self.buffer_size = 150
        self.count = 0
        self.i0_buffer = collections.deque([0]*self.buffer_size, self.buffer_size)
        self.diff_buffer = collections.deque([0]*self.buffer_size, self.buffer_size)
        self.ratio_buffer = collections.deque([0]*self.buffer_size, self.buffer_size)
        self.calibration_value = 0
        self.i0_rdbutton_selection = 'gatt'

        self.rdbuttonstatus.connect(self.update_rdbutton)
        self.signals.mode.connect(self.update_mode)
        self.signals.nsamp.connect(self.update_nsamp)

    def reset_buffers(self, size):
        self.buffer_size = size
        self._initial_intensity_buffer = collections.deque([0]*self.buffer_size, self.buffer_size)

    def update_mode(self, mode):
        self.mode = mode

    def update_nsamp(self, nsamp):
        self.nsamp = nsamp

    def update_rdbutton(self, rdbutton):
        self.i0_rdbutton_selection = rdbutton

    def run(self):
        while not self.interruptedRequested():
             new_values = ValueReader().read_value()
             if self.mode == 'Running':
                 if self.count < self.buffer_size:
                     self.count += 1
                     self.i0_buffer.append(new_values.get(self.i0_rdbutton_selection))
                     self.diff_buffer.append(new_values.get('diffraction')
                     self.ratio_buffer.append(self.i0_buffer[-1]/self.diff_buffer[-1])
                 else: 
                     new_status = self.compare(new_values)
                     self.i0_buffer.append(new_values.get(self.i0_rdbutton_selection))
                     self.diff_buffer.append(new_values.get('diffraction')
                     self.ratio_buffer.append(self.i0_buffer[-1]/self.diff_buffer[-1])
             else:
                 self.calibrate(new_values)
             self.signals.values.emit([self.i0_buffer, self.diff_buffer, self.ratio_buffer])
             self.signals.status.emit(new_status)
             self.sleep(300)
         self.count = 0
              
    def compare(self, new_values):
        pass
    
    def calibration(self, values):
        
        self.calibration_value.emit(calibration_value)
                   

class GraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.setMouseTracking(True)


class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(GraphicsScene, self).__init__(parent)
        # self.thread = thread()


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

    def __init__(self, parent=None, args=None, macros=None):
        super(JetTracking, self).__init__(parent=parent, args=args, macros=macros)

        # reference to PyDMApplication - this line is what makes it so that you
        # #can avoid having to define main() and instead pydm handles that
        # for you - it is a subclass of QWidget
        self.app = QApplication.instance()
        
        # load data from file
        self.load_data()

        self.signals = Signals()
        self.calibration = Calibration(self.signals, self)
        
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
        self._layout.addStretch(1)
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

        self.bttngrp = QButtonGroup()
        self.rdbttn_live = QRadioButton("live data")  # .setChecked(True)
        self.rdbttn_sim = QRadioButton("simulated data")  # .setChecked(False)
        self.rdbttn_live.setChecked(True)
        self.bttngrp.addButton(self.rdbttn_live)
        self.bttngrp.addButton(self.rdbttn_sim)
        self.bttngrp.setExclusive(True)  # allows only one button to be selected at a time

        # setup layout
        ##############
        self.frame_rdbttns = QFrame()
        self.layout_rdbttns = QHBoxLayout()
        self.frame_rdbttns.setLayout(self.layout_rdbttns)
        self.layout_usr_cntrl.addWidget(self.frame_rdbttns)
        self.layout_rdbttns.addWidget(self.rdbttn_live)
        self.layout_rdbttns.addWidget(self.rdbttn_sim)

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

        self.cali_i0 = self.calibration.get_i0()
        self.lbl_i0_status.display(self.cali_i0)

        self.lbl_diff_i0 = Label("Diffraction at detector")
        self.lbl_diff_i0.setSubtitleStyleSheet()
        self.lbl_diff_i0_status = QLCDNumber(4)

        self.diff_i = self.calibration.get_diff()
        self.lbl_diff_i0_status.display(self.diff_i)

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
        self.frame_diff_i0.layout().addWidget(self.lbl_diff_i0_status)

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
        self.layout_main.addWidget(self.frame_graph)
        self.layout_main.addWidget(self.frame_usr_cntrl)

        self.graph_setup()
        

        ###################################################
        # signals and slots
        ###################################################
        #self.bttn_calibrate.clicked.connect(###)
        self.bttn_start.clicked.connect(self.handle_start)
        self.bttn_stop.clicked.connect(self.handle_stop)
        self.signals.stopped.connect(self.counterThread.quit)
        self.cbox_sigma.activated.connect(self.update_sigma)
        self.cbox_nsamp.activated.connect(self.update_nsamp)
        self.bttngrp.buttonClicked.connect(self.checkBttn)

        self.signals.params.connect(self.update_data)
        self.counterThread.started.connect(self.counter.start)

        self.signals.status.connect(self.update_status)

        ###################################################

    def handle_start(self):
        self.status_thread = StatusThread()
        ### connect signals and slots on this class
        self.status_thread.start()

    def handle_stop(self):
        self.status_thread.requestInterrupt()
        if self.correction_thread is not None:
            self.correction_thread.requestInterrupt()

    def receive_values(self, values):

        ## update plots and line edits

    def receive_status(self, status):
        if status == 'outside':
           if self.correction_thread is None:
               #avoid issues with fluctuations and multiple corrections
               self.correction_thread = correctionThread()
               self.correction_thread.finished.connect(self.cleanup_correction)
               self.correction_thread.start()
    
    def cleanup_correction(self):
       self.correction_thread = None

    def combo_samples_change(self, value):
       self.status_thread.reset_buffers(value)

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



'''

    def update_status(self, value):

        if value == 0:
            self.lbl_tracking_status.setText("No Tracking")
            self.lbl_tracking_status.setStyleSheet("\
                background-color: red;")

        elif value == 1:
            self.lbl_tracking_status.setText("Tracking")
            self.lbl_tracking_status.setStyleSheet("\
                background-color: green;")

        elif value == 2:
            self.lbl_tracking_status.setText("Warning! Low incoming intensity")
            self.lbl_tracking_status.setStyleSheet("\
                background-color: yellow;")

        elif value == 3:
            self.lbl_tracking_status.setText("Warning! check jet alignment")
            self.lbl_tracking_status.setStyleSheet("\
                background-color: orange;")

    def update_sigma(self, sigma):
        self.signals.sigma.emit(float(self.cbox_sigma.currentText()))

    def update_nsamp(self):
        # nsamp = self.tbox_nsamp.text()
        # print(nsamp, type(nsamp))
        self.signals.nsamp.emit(float(self.cbox_nsamp.currentText()))

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

    def graph_setup(self):

        self.gr = graphDisplay(self.signals, self.calibration)
        self.gr.create_plots(self.view_graph1, self.view_graph2, self.view_graph3)

    def update_data(self, data):

        self.gr.plot_scroll(data)

    def checkBttn(self, button):
        bttn = button.text()

        if bttn == "simulated data":
            print(bttn)
            self.pyqtGraphing()
            self.signals.rdbttnStatus.emit(1)
            self.mode = 1

        if bttn == "live data":
            print(bttn)
            self.liveGraphing()
            self.signals.rdbttnStatus.emit(0)
            self.mode = 0

    def pyqtGraphing(self):

        self.clearLayout(self.layout_graph)

        self.view_graph1 = pg.PlotWidget()
        self.view_graph2 = pg.PlotWidget()
        self.view_graph3 = pg.PlotWidget()

        self.layout_graph.addWidget(self.view_graph1)
        self.layout_graph.addWidget(self.view_graph2)
        self.layout_graph.addWidget(self.view_graph3)

        self.graph_setup()

    def liveGraphing(self):

        self.clearLayout(self.layout_graph)

        self.view_graph1 = pg.PlotWidget()
        self.view_graph2 = pg.PlotWidget()
        self.view_graph3 = pg.PlotWidget()

        self.layout_graph.addWidget(self.view_graph1)
        self.layout_graph.addWidget(self.view_graph2)
        self.layout_graph.addWidget(self.view_graph3)

        self.graph_setup()

    def clearLayout(self, layout):

        for i in reversed(range(layout.count())):
            widgetToRemove = layout.itemAt(i).widget()
            layout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)
'''
