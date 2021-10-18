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
        #parsed_args, unparsed_args = self.read_args()

        #  calibration values
        self.hutch = ' ' #default is CXI
        self.i0_low = 0
        self.i0_high = 0
        self.i0_med = 0
        self.peak_bin = 0
        self.delta_bin = 0
        self.mean_ratio = 0
        self.med_ratio = 0
        self.std_ratio = 0
        self.jet_loc_mean = 0
        self.jet_loc_std = 0
        self.jet_peak_mean = 0
        self.jet_peak_std = 0
        
        self.calibration_values = {}

        self.signals = Signals()
        self.worker = StatusThread(self.signals)
        self.thread_options = {}

        self.worker_motor = None
        self.motor_options = {}

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
        self.liveGraphing()

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
        self.rdbttn_cali_live = QRadioButton("Calibration in GUI")
        self.rdbttn_cali = QRadioButton("Calibration from Results")
        self.rdbttn_cali.setChecked(True)
        self.bttngrp3.addButton(self.rdbttn_cali, id=0)
        self.bttngrp3.addButton(self.rdbttn_cali_live, id=1)
        self.bttngrp3.setExclusive(True)

        self.thread_options['calibration source'] = self.bttngrp3.checkedId()        

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
        # make input box for changing nsampning for sigma
        #####################################################################

        self.lbl_sigma = Label("Sigma \n(0.1 - 5)")
        self.le_sigma = LineEdit("2")
        self.le_sigma.valRange(0.1, 5.0)

        self.lbl_ave_graph = Label('averaging (graph) \n(5 - 300)')
        self.lbl_samprate = Label('sampling rate \n(2 - 300)')
        self.le_ave_graph = LineEdit("50")
        self.le_ave_graph.valRange(5, 300)
        self.le_samprate = LineEdit("50")
        self.le_samprate.valRange(2, 300)

        self.thread_options['sigma'] = float(self.le_sigma.text())
        self.thread_options['averaging'] = float(self.le_ave_graph.text())
        self.thread_options['sampling rate'] = float(self.le_samprate.text())

        # setup layout
        ##############
        self.frame_samp = QFrame()
        self.layout_samp = QHBoxLayout()
        self.frame_samp.setLayout(self.layout_samp)
        self.layout_usr_cntrl.addWidget(self.frame_samp)
        self.layout_samp.addWidget(self.lbl_sigma)
        self.layout_samp.addWidget(self.le_sigma)
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

        self.thread_options['manual motor'] = self.bttngrp2.checkedId()

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

        self.motor_options['high limit'] = float(self.le_motor_hl.text())
        self.motor_options['low limit'] = float(self.le_motor_ll.text())
        self.motor_options['step size'] = float(self.le_size.text())
        self.motor_options['averaging'] = float(self.le_ave_motor.text())
        self.motor_options['scanning algorithm'] = self.cbox_algorithm.currentIndex()

        self.bttn_search = QPushButton()
        self.bttn_search.setText("Search")
        self.bttn_search.setEnabled(False) 

        self.bttn_tracking = QPushButton()
        self.bttn_tracking.setText("Track")
        self.bttn_tracking.setEnabled(False)

        self.bttn_stop_tracking = QPushButton()
        self.bttn_stop_tracking.setText("Stop Tracking")
        self.bttn_stop_tracking.setEnabled(False)

        self.frame_motor = QFrame()
        self.layout_motor = QVBoxLayout()
        self.layout_motor_manual = QHBoxLayout()
        self.layout_motor_input = QGridLayout()
        self.layout_motor_bttns = QHBoxLayout()
        self.layout_motor.addLayout(self.layout_motor_manual)
        self.layout_motor.addLayout(self.layout_motor_input)
        self.layout_motor.addLayout(self.layout_motor_bttns)
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
        self.layout_motor_bttns.addWidget(self.bttn_stop_tracking)
        

        #####################################################################
        # give a status area that displays values and current tracking
        # reliability based on various readouts
        #####################################################################

        self.lbl_status = Label("Status")
        self.lbl_status.setTitleStylesheet()

        self.lbl_tracking = Label("Tracking")
        self.lbl_tracking.setSubtitleStyleSheet()
        self.lbl_tracking_status = Label("No Tracking")

        self.lbl_i0 = Label("Mean Initial intensity (I0)")
        self.lbl_i0_status = QLCDNumber(7)

        self.lbl_diff_i0 = Label("Mean I/I0")
        self.lbl_diff_status = QLCDNumber(7)

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

        self.graph_setup()


        ###################################################
        # signals and slots
        ###################################################
        self.le_sigma.checkVal.connect(self.update_sigma)
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
        self.signals.status.connect(self.update_status)
        self.signals.calibration_value.connect(self.update_calibration)

        self.bttn_search.clicked.connect(self._start_search)
        self.bttn_tracking.clicked.connect(self._start_tracking)
        self.bttn_stop_tracking.clicked.connect(self._stop_tracking)

        self.signals.status.connect(self.update_status)
        self.signals.buffers.connect(self.plot_data)
        self.signals.avevalues.connect(self.plot_ave_data)

        self.signals.finished.connect(self._motor_stop)
        self.signals.message.connect(self.receive_message)
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

    def _motor_stop(self, vals):
        self.text_area.append("motor position: " + vals['position'])
        self.text_area.append("peak intensity: " + vals['ratio'])
        self.worker_motor.requestInterruption()
        self.worker_motor.wait()

    def _calibrate(self):
        button = self.bttngrp3.checkedButton()
        button_text = button.text()
        print(button_text)
        if self.bttngrp3.checkedButton().text() == "Calibration from Results":
            print("I am calibrating from results")
            self.signals.mode.emit("get calibration")
        elif self.bttngrp3.checkedButton().text() == "Calibration in GUI":
            print("I am calibrating from the GUI")
            self.signals.mode.emit("calibration")
        self.text_area.append("obtaining calibration values... ")
        self._start()

    def _start_search(self):
        if self.worker.isRunning():
            self.worker_motor = MotorThread(self.signals, "search")
            self.worker_motor.start()
        else:
            self.text_area.append("there's nothing to scan!")

    def _start_tracking(self):
        self.signals.motormove.emit(1)

    def _stop_tracking(self):
        self.signals.motormove.emit(2)

    def update_calibration(self, cal):
        print(cal)
        self.lbl_i0_status.display(cal['i0']['mean'])
        self.lbl_diff_status.display(cal['ratio']['mean'])
        

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
        self.xRange = 300
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
                                           size=1)
        self.plot1cali = pg.PlotCurveItem(pen=pg.mkPen(width=1, color=(255, 255, 0)),
                                           size=1, style=Qt.DashLine)
        self.plot1sigmalow = pg.PlotCurveItem(pen=pg.mkPen(width=1, color=(255, 255, 0)),
                                           size=1, style=Qt.DashLine)
        self.plot1sigmahigh = pg.PlotCurveItem(pen=pg.mkPen(width=1, color=(255, 255, 0)),
                                           size=1, style=Qt.DashLine)
        self.graph1.addItem(self.plot1ave)
        self.graph1.addItem(self.plot1cali)
        self.graph1.addItem(self.plot1sigmalow)
        self.graph1.addItem(self.plot1sigmahigh)
        self.cali = []
        self.sigma = []
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
        #self.cali.append(
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
        self.signals.sigma.emit(sigma)

    def update_nsamp(self, nsamp):
        self.signals.nsampval.emit(nsamp)

    def update_samprate(self, samprate):
        self.signals.samprate.emit(samprate)

    def update_limits(self, limit):
        self.signals.limits.emit(float(self.le_motor_ll.text()), float(self.le_motor_hl.text()))

    def update_tol(self, tol):
        print(tol)
        self.signals.tol.emit(tol)

    def receive_message(self, message):
        self.text_area.append(message)

    def cleanup_correction(self):
       self.signals.correction_thread = None
       self.thread.reset_buffers(value)

    def checkBttn(self, button):
        bttn = button.text()
        if bttn == "simulated data":
            self.rdbttn_manual.click()
            self.rdbttn_auto.setEnabled(False)
            self.signals.run_live.emit(0)
        elif bttn == "live data":
            self.rdbttn_auto.setEnabled(True)
            self.signals.run_live.emit(1)
        elif bttn == "manual motor moving":
            self.bttn_search.setEnabled(False)
            self.bttn_tracking.setEnabled(False)
            self.bttn_stop_tracking.setEnabled(False)
        elif bttn == "automated motor moving":
            self.bttn_search.setEnabled(True)
            self.bttn_tracking.setEnabled(True)
            self.bttn_stop_tracking.setEnabled(True)
    
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

