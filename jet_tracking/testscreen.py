import collections
import logging
import threading
import time
import argparse
from statistics import mean, stdev

import numpy as np
import pyqtgraph as pg
import zmq
from datastream import StatusThread, ValueReader, MotorThread
from num_gen import *
from ophyd import EpicsSignal
from pydm import Display
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qtpy import QtCore
from qtpy.QtCore import *
from qtpy.QtWidgets import (QApplication, QFrame, QGraphicsScene,
                            QGraphicsView, QHBoxLayout, QLabel, QPushButton,
                            QVBoxLayout)

from signals import Signals
from jetgraphing import ScrollingTimeWidget, graph_setup, add_calibration_graph

logging = logging.getLogger('pydm')
logging.setLevel('CRITICAL')

lock = threading.Lock()

JT_LOC = '/cds/group/pcds/epics-dev/aegger/jet_tracking/jet_tracking/'
SD_LOC = '/reg/d/psdm/'

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

class LineEdit(QLineEdit):
    checkVal = pyqtSignal(float)
    def __init__(self, *args, **kwargs):
        super(LineEdit, self).__init__(*args, **kwargs)
        self.validator = QDoubleValidator()
        self.setValidator(self.validator)
        self.textChanged.connect(self.new_text)
        self.returnPressed.connect(self.check_validator)
        self.ntext = self.text()

    def new_text(self, text):
        if self.hasAcceptableInput():
            self.ntext = text

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Return and not self.hasAcceptableInput():
            self.check_validator()

    def check_validator(self):
        try:
            if float(self.text()) > self.validator.top():
                self.setText(str(self.validator.top()))
            elif float(self.text()) < self.validator.bottom():
                self.setText(str(self.validator.bottom()))
        except:
            mssg = QMessageBox.about(self, "Error", "Input can only be a number")
            self.setText(self.ntext)
        self.checkVal.emit(float(self.ntext))

    def valRange(self, x1, x2):
        self.validator.setRange(x1, x2)
        self.validator.setDecimals(6)
        self.validator.setNotation(QDoubleValidator.StandardNotation)

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
        #parsed_args, unparsed_args = self.read_args()
        self.SIGNALS = Signals()
       
        self.hutch = ' '
        self.calibrated = False

        self.thread_options = {}
        #  keys:
        #  live graphing
        #  calibration source
        #  percent
        #  averaging
        #  sampling rate
        #  manual motor

        self.worker_motor = MotorThread(self.SIGNALS)
        self.motor_options = {}
        #  keys:
        #  high limit
        #  low limit
        #  step size
        #  averaging
        #  scanning algorithm

        self.worker = StatusThread(self.SIGNALS)

        # assemble widgets
        self.setup_ui()

    def minimumSizeHint(self):

        return(QtCore.QSize(1400, 800))

    def ui_filepath(self):

        # no Ui file is being used as of now
        pass

    def read_args(self):
        pass
        

        """ 
        print("hi")
        parser = argparse.ArgumentParser(description = "Description for my parser")
        parser.add_argument("-H", "--Help", help = "Example: Help argument", required = False, default = "")
        parser.add_argument("-s", "--save", help = "Example: Save argument", required = False, default = "")
        parser.add_argument("-p", "--print", help = "Example: Print argument", required = False, default = "")
        parser.add_argument("-o", "--output", help = "Example: Output argument", required = False, default = "")

        parsed_args, unparsed_args = parser.parse_known_args()
        status = False
        print(parsed_args)
        if parsed_args.Help:
            print("You have used '-H' or '--Help' with argument: {0}".format(argument.Help))
            status = True
        if parsed_args.save:
            print("You have used '-s' or '--save' with argument: {0}".format(argument.save))
            status = True
        if parsed_args.print:
            print("You have used '-p' or '--print' with argument: {0}".format(argument.print))
            status = True
        if parsed_args.output:
            print("You have used '-o' or '--output' with argument: {0}".format(argument.output))
            status = True
        if not status:
            print("Maybe you want to use -H or -s or -p or -p as arguments ?")
        return(parsed_args, unparsed_args)
        """

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
        self.live_graphing()

        #####################################################################
        # set up user panel layout and give it a title
        #####################################################################
        self.frame_usr_cntrl = QFrame()
        self.frame_usr_cntrl.setMinimumHeight(500)
        self.layout_usr_cntrl = QVBoxLayout()
        self.frame_usr_cntrl.setLayout(self.layout_usr_cntrl)

        self.lbl_usr_cntrl = Label("Graphing/Data Controls")
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
        self.bttngrp1.addButton(self.rdbttn_live, id=1)
        self.bttngrp1.addButton(self.rdbttn_sim, id=0)
        self.bttngrp1.setExclusive(True)  # allows only one button to be selected at a time
 
        self.bttngrp3 = QButtonGroup()
        self.rdbttn_cali_live = QRadioButton("calibration in GUI")
        self.rdbttn_cali = QRadioButton("calibration from results")
        self.rdbttn_cali.setChecked(True)
        self.bttngrp3.addButton(self.rdbttn_cali, id=0)
        self.bttngrp3.addButton(self.rdbttn_cali_live, id=1)
        self.bttngrp3.setExclusive(True)

        # setup layout
        ##############
        self.frame_rdbttns = QFrame()
        self.layout_allrdbttns = QGridLayout()
        self.layout_allrdbttns.setColumnStretch(0, 1)
        self.layout_allrdbttns.setColumnStretch(1, 1)
        self.layout_allrdbttns.setColumnStretch(2, 1)
        self.frame_rdbttns.setLayout(self.layout_allrdbttns)
        self.layout_usr_cntrl.addWidget(self.frame_rdbttns)
        self.layout_allrdbttns.addWidget(self.rdbttn_live, 0, 0)
        self.layout_allrdbttns.addWidget(self.rdbttn_sim, 0, 1)
        self.layout_allrdbttns.addWidget(self.rdbttn_cali, 1, 0)
        self.layout_allrdbttns.addWidget(self.rdbttn_cali_live, 1, 1) 

        #####################################################################
        # make input box for changing the percent of allowed values from the
        # mean and the number of points for averaging on the graph and the 
        # refresh rate to update the points/graph
        #####################################################################

        self.lbl_percent = Label("Percent \n(0 - 100)")
        self.le_percent = LineEdit("70")
        self.le_percent.valRange(0, 100)
        
        self.lbl_ave_graph = Label('averaging (graph) \n(5 - 300)')
        self.lbl_samprate = Label('sampling rate \n(2 - 300)')
        self.le_ave_graph = LineEdit("50")
        self.le_ave_graph.valRange(5, 300)
        self.le_samprate = LineEdit("50")
        self.le_samprate.valRange(2, 300)

        # setup layout
        ##############
        self.frame_samp = QFrame()
        self.layout_samp = QHBoxLayout()
        self.frame_samp.setLayout(self.layout_samp)
        self.layout_usr_cntrl.addWidget(self.frame_samp)
        self.layout_samp.addWidget(self.lbl_percent)
        self.layout_samp.addWidget(self.le_percent)
        self.layout_samp.addWidget(self.lbl_ave_graph)
        self.layout_samp.addWidget(self.le_ave_graph)
        self.layout_samp.addWidget(self.lbl_samprate)
        self.layout_samp.addWidget(self.le_samprate)

        ###################################################################
        #  make section for editing motor parameters
        ###################################################################

        self.lbl_motor = Label("Motor Parameters (microns)")
        self.lbl_motor.setTitleStylesheet()
        self.layout_usr_cntrl.addWidget(self.lbl_motor)

        self.bttngrp2 = QButtonGroup()
        self.rdbttn_manual = QRadioButton("manual motor moving")  # .setChecked(True)
        self.rdbttn_auto = QRadioButton("automated motor moving")  # .setChecked(False)
        self.rdbttn_manual.setChecked(True)
        self.bttngrp2.addButton(self.rdbttn_manual, id= 1)
        self.bttngrp2.addButton(self.rdbttn_auto, id = 0)
        self.bttngrp2.setExclusive(True)  # allows only one button to be selected at a time

        self.lbl_motor_hl = Label("High Limit")
        self.lbl_motor_ll = Label("Low Limit")
        self.lbl_motor_size = Label("Step Size")
        self.lbl_motor_average = Label("Average Intensity")
        self.lbl_algorithm = Label("Algorithm")        

        self.le_motor_hl = LineEdit("50")
        self.le_motor_hl.valRange(-100, 100)

        self.le_motor_ll = LineEdit("-50")
        self.le_motor_ll.valRange(-100, 100)

        self.le_size = LineEdit(".5")
        self.le_size.valRange(0, 100)

        self.le_ave_motor = LineEdit("10")
        self.le_ave_motor.valRange(1, 300)

        self.cbox_algorithm = ComboBox()
        self.cbox_algorithm.addItem("Ternary Search")
        self.cbox_algorithm.addItem("Full Scan")

        self.bttn_search = QPushButton()
        self.bttn_search.setText("Search")
        self.bttn_search.setEnabled(False) 

        self.bttn_tracking = QPushButton()
        self.bttn_tracking.setText("Track")
        self.bttn_tracking.setEnabled(False)

        self.bttn_stop_motor = QPushButton()
        self.bttn_stop_motor.setText("Stop Tracking")
        self.bttn_stop_motor.setEnabled(False)

        self.lbl_tracking = Label("Tracking")
        self.lbl_tracking.setSubtitleStyleSheet()
        self.lbl_tracking_status = Label("False")
        self.lbl_tracking_status.setStyleSheet(f"\
                background-color: red;")

        self.frame_motor = QFrame()
        self.layout_motor = QVBoxLayout()
        self.layout_motor_manual = QHBoxLayout()
        self.layout_motor_input = QGridLayout()
        self.layout_motor_bttns = QHBoxLayout()
        self.layout_tracking = QHBoxLayout()
        self.layout_motor.addLayout(self.layout_motor_manual)
        self.layout_motor.addLayout(self.layout_motor_input)
        self.layout_motor.addLayout(self.layout_motor_bttns)
        self.layout_motor.addLayout(self.layout_tracking)
        self.frame_motor.setLayout(self.layout_motor)
        self.layout_usr_cntrl.addWidget(self.frame_motor)
        self.layout_motor_manual.addWidget(self.rdbttn_manual)
        self.layout_motor_manual.addWidget(self.rdbttn_auto)
        self.layout_motor_input.addWidget(self.lbl_motor_ll, 0, 0)
        self.layout_motor_input.addWidget(self.le_motor_ll, 0, 1)
        self.layout_motor_input.addWidget(self.lbl_motor_hl, 0, 2)
        self.layout_motor_input.addWidget(self.le_motor_hl, 0, 3)
        self.layout_motor_input.addWidget(self.lbl_motor_size, 1, 0)
        self.layout_motor_input.addWidget(self.le_size, 1, 1)
        self.layout_motor_input.addWidget(self.lbl_motor_average, 1, 2)
        self.layout_motor_input.addWidget(self.le_ave_motor, 1, 3)
        self.layout_motor_input.addWidget(self.lbl_algorithm, 2, 0)
        self.layout_motor_input.addWidget(self.cbox_algorithm, 2, 1)
        self.layout_motor_bttns.addWidget(self.bttn_search)
        self.layout_motor_bttns.addWidget(self.bttn_tracking)
        self.layout_motor_bttns.addWidget(self.bttn_stop_motor)
        self.layout_tracking.addWidget(self.lbl_tracking)
        self.layout_tracking.addWidget(self.lbl_tracking_status)

        #####################################################################
        # give a status area that displays values and current tracking
        # reliability based on various readouts
        #####################################################################

        self.lbl_status = Label("Status")
        self.lbl_status.setTitleStylesheet()

        self.lbl_monitor = Label("Monitor")
        self.lbl_monitor.setSubtitleStyleSheet()
        self.lbl_monitor_status = Label("Not Started")

        self.lbl_i0 = Label("Mean Initial intensity (I0)")
        self.lbl_i0_status = QLCDNumber(7)

        self.lbl_diff_i0 = Label("Mean I/I0")
        self.lbl_diff_status = QLCDNumber(7)

        # setup layout
        ##############
        self.layout_usr_cntrl.addWidget(self.lbl_status)

        self.frame_monitor_status = QFrame()
        self.frame_monitor_status.setLayout(QHBoxLayout())
        self.frame_monitor_status.layout().addWidget(self.lbl_monitor)
        self.frame_monitor_status.layout().addWidget(self.lbl_monitor_status)

        self.frame_i0 = QFrame()
        self.frame_i0.setLayout(QHBoxLayout())
        self.frame_i0.layout().addWidget(self.lbl_i0)
        self.frame_i0.layout().addWidget(self.lbl_i0_status)

        self.frame_diff_i0 = QFrame()
        self.frame_diff_i0.setLayout(QHBoxLayout())
        self.frame_diff_i0.layout().addWidget(self.lbl_diff_i0)
        self.frame_diff_i0.layout().addWidget(self.lbl_diff_status)

        self.layout_usr_cntrl.addWidget(self.frame_monitor_status)
        self.layout_usr_cntrl.addWidget(self.frame_i0)
        self.layout_usr_cntrl.addWidget(self.frame_diff_i0)
        ###############################

        ########################################################################
        # text area for giving updates the user can see
        ########################################################################

        self.text_area = QTextEdit("~~~read only information for user~~~")
        #self.text_area.append("To run in live mode, please select the hutch this program is currently being used in")
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

        ##################################################
        #  tracking values
        ##################################################

        self.thread_options['live graphing'] = self.bttngrp1.checkedId()
        self.thread_options['calibration source'] = self.bttngrp3.checkedId()
        self.thread_options['percent'] = float(self.le_percent.text())
        self.thread_options['averaging'] = float(self.le_ave_graph.text())
        self.thread_options['sampling rate'] = float(self.le_samprate.text())
        self.thread_options['manual motor'] = self.bttngrp2.checkedId()

        self.motor_options['high limit'] = float(self.le_motor_hl.text())
        self.motor_options['low limit'] = float(self.le_motor_ll.text())
        self.motor_options['step size'] = float(self.le_size.text())
        self.motor_options['averaging'] = float(self.le_ave_motor.text())
        self.motor_options['scanning algorithm'] = self.cbox_algorithm.currentIndex()

        ###################################################
        # SIGNALS and slots
        ###################################################
        self.le_percent.checkVal.connect(self.update_percent)
        self.le_samprate.checkVal.connect(self.update_samprate)
        self.le_ave_graph.checkVal.connect(self.update_nsamp)
        self.le_motor_ll.checkVal.connect(self.update_limits)
        self.le_motor_hl.checkVal.connect(self.update_limits)
        self.le_size.checkVal.connect(self.update_tol)
        self.bttngrp1.buttonClicked.connect(self.checkBttn)
        self.bttngrp2.buttonClicked.connect(self.checkBttn)
        self.bttngrp3.buttonClicked.connect(self.checkBttn)

        self.bttn_start.clicked.connect(self._start)
        self.bttn_stop.clicked.connect(self._stop)
        self.bttn_calibrate.clicked.connect(self._calibrate)
        self.SIGNALS.calibration_value.connect(self.update_calibration)

        self.bttn_search.clicked.connect(self._start_motor)
        self.bttn_tracking.clicked.connect(self._enable_tracking)
        self.bttn_stop_motor.clicked.connect(self._stop_motor)

        self.SIGNALS.status.connect(self.update_monitor_status)
        self.SIGNALS.buffers.connect(self.plot_data)
        self.SIGNALS.avevalues.connect(self.plot_ave_data)

        self.SIGNALS.wake.connect(self._start_motor)
        self.SIGNALS.sleep.connect(self._stop_motor)
        self.SIGNALS.message.connect(self.receive_message)
        ###################################################

    def _start(self):
        ## check if thread is running
        ## if it is we don't want to restart it! we might want to change the mode though
        ## if not start the thread
        ## if thread is running start is pressed do nothing
        self.SIGNALS.threadOp.emit(self.thread_options)
        self.worker.start()

    def _stop(self):
        if self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()

    def _calibrate(self):
        if not self.worker.isRunning():
            self.text_area.append("You are not running so there's \
                  nothing to calibrate.. hit start first")
        else:
            self.SIGNALS.threadOp.emit(self.thread_options)
            self.SIGNALS.mode.emit("calibrate")

    def _enable_tracking(self):
        self.update_tracking_status("enabled", green)
        self.isTracking = True
        self._start_motor()

    def _start_motor(self):
        if not self.worker_motor.isRunning():
            if self.worker.isRunning():
                self.SIGNALS.motorOp.emit(self.motor_options)
                self.SIGNALS.mode.emit("correcting")
                self.worker_motor.start()
            else:
                self.text_area.append("there's nothing to scan!")
        else:
            if self.worker_motor.isInterruptionRequested():
                self.SIGNALS.motorOp.emit(self.motor_options)
                self.worker_motor.start()
            else:
                self.text_area.append("The motor is already running")

    def _stop_motor(self):
        if self.worker_motor.isRunning():
            self.worker_motor.requestInterruption()
            self.worker_motor.wait()
        if self.sender() is self.bttn_stop_motor:
            self.isTracking = False
            self.update_tracking_status('disabled', red)

    def update_calibration(self, cal): 
        self.calibration_values = cal
        self.lbl_i0_status.display(self.calibration_values['i0']['mean'])
        self.lbl_diff_status.display(self.calibration_values['diff']['mean'])
        add_calibration_graph(self.ratio_graph)
        add_calibration_graph(self.i0_graph)
        add_calibration_graph(self.diff_graph)
        self.calibrated = True 

    def live_graphing(self):
        self.clearLayout(self.layout_graph)

        self.ratio_graph = ScrollingTimeWidget(self.SIGNALS)
        self.i0_graph = ScrollingTimeWidget(self.SIGNALS)
        self.diff_graph = ScrollingTimeWidget(self.SIGNALS)

        graph_setup(self.ratio_graph, "Intensity Ratio", f"I/I\N{SUBSCRIPT ZERO}", \
                        pg.mkPen(width=5, color='r'))
        graph_setup(self.i0_graph, "Initial Intensity", f"I\N{SUBSCRIPT ZERO}", \
                        pg.mkPen(width=5, color='b'))
        graph_setup(self.diff_graph, "Intensity at the Detector", "Diffraction Intensity", \
                        pg.mkPen(width=5, color='g'))  
        self.i0_graph.setXLink(self.ratio_graph)
        self.diff_graph.setXLink(self.ratio_graph)
        self.layout_graph.addWidget(self.ratio_graph)
        self.layout_graph.addWidget(self.i0_graph)
        self.layout_graph.addWidget(self.diff_graph)

    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            widgetToRemove = layout.itemAt(i).widget()
            layout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

    def plot_data(self, data):
        self.ratio_graph.plt.setData(list(data['time']), list(data['ratio']))
        self.ratio_graph.setXRange(list(data['time'])[0], list(data['time'])[-1])
        self.i0_graph.plt.setData(list(data['time']), list(data['i0']))
        self.diff_graph.plt.setData(list(data['time']), list(data['diff']))
        if self.calibrated:
            self.diff_graph.percent_low.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['diff']['range'][0]]*300, 300))) 
            self.diff_graph.percent_high.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['diff']['range'][1]]*300, 300)))
            self.diff_graph.mean_plt.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['diff']['mean']]*300, 300)))
            self.ratio_graph.percent_low.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['ratio']['range'][0]]*300, 300)))
            self.ratio_graph.percent_high.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['ratio']['range'][1]]*300, 300)))
            self.ratio_graph.mean_plt.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['ratio']['mean']]*300, 300)))
            self.i0_graph.percent_low.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['i0']['range'][0]]*300, 300)))
            self.i0_graph.percent_high.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['i0']['range'][1]]*300, 300)))
            self.i0_graph.mean_plt.setData(list(data['time']), list(collections.deque(\
                  [self.calibration_values['i0']['mean']]*300, 300)))

    def plot_ave_data(self, data):
        self.ratio_graph.avg_plt.setData(list(data['time']), list(data['average ratio']))
        self.i0_graph.avg_plt.setData(list(data['time']), list(data['average i0']))
        self.diff_graph.avg_plt.setData(list(data['time']), list(data['average diff']))

    def update_tracking_status(self, status, color):
        self.lbl_tracking_status.setText(status)
        self.lbl_tracking_status.setStyleSheet(f"\
                background-color: {color};")
        self.SIGNALS.enable_tracking.emit(self.isTracking)

    def update_monitor_status(self, status, color):
        self.lbl_monitor_status.setText(status)
        self.lbl_monitor_status.setStyleSheet(f"\
                background-color: {color};")

    def receive_status(self, status):
        if status == 'outside':
           if self.correction_thread is None:
               #avoid issues with fluctuations and multiple corrections
               self.correction_thread = correctionThread()
               self.correction_thread.finished.connect(self.cleanup_correction)
               self.correction_thread.start()

    def update_percent(self, percent):
        self.thread_options['percent'] = percent
        self.SIGNALS.threadOp.emit(self.thread_options)
        if self.calibrated:
            self.SIGNALS.mode.emit('calibrate')

    def update_nsamp(self, nsamp):
        self.thread_options['average'] = nsamp
        self.SIGNALS.threadOp.emit(self.thread_options)

    def update_samprate(self, samprate):
        self.thread_options['sampling rate'] = samprate
        self.SIGNALS.threadOp.emit(self.thread_options)

    def update_limits(self, limit):
        self.motor_options['high limit'] = float(self.le_motor_hl.text())
        self.motor_options['low limit'] = float(self.le_motor_ll.text())
        self.SIGNALS.motorOp.emit(self.motor_options)

    def update_tol(self, tol):
        self.motor_options['step size'] = float(tol)
        self.SIGNALS.motorOp.emit(self.motor_options)

    def update_motor_avg(self, avg):
        self.motor_options['averaging'] = float(avg)
        self.SIGNALS.motorOp.emit(self.motor_options)

    def update_algorithm(self, alg): 
        self.motor_options['scanning algorithm'] = self.cbox_algorithm.currentIndex()
        self.SIGNALS.motorOp.emit(self.motor_options)

    def receive_message(self, message):
        self.text_area.append(message)

    def cleanup_correction(self):
       self.SIGNALS.correction_thread = None
       self.thread.reset_buffers(value)

    def checkBttn(self, button):
        bttn = button.text()
        if bttn == "simulated data":
            self.rdbttn_manual.click()
            self.rdbttn_auto.setEnabled(False)
            self.SIGNALS.run_live.emit(0)
        elif bttn == "live data":
            self.rdbttn_auto.setEnabled(True)
            self.SIGNALS.run_live.emit(1)
        elif bttn == "manual motor moving":
            self.bttn_search.setEnabled(False)
            self.bttn_tracking.setEnabled(False)
            self.bttn_stop_motor.setEnabled(False)
        elif bttn == "automated motor moving":
            self.bttn_search.setEnabled(True)
            self.bttn_tracking.setEnabled(True)
            self.bttn_stop_motor.setEnabled(True)
        elif bttn == "calibration in GUI":
            self.thread_options['calibration source'] = bttn
        elif bttn == "calibration from results":
            self.thread_options['calibration source'] = bttn

    
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

