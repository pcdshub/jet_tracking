import time

from pydm import Display
from qtpy.QtCore import QThread
from os import path

import os
import json
import cv2
import numpy as np
import zmq

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from qtpy import QtCore
from pydm import Display
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QWidget, QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
    QGraphicsItem, QSizePolicy)
import pyqtgraph as pg

from pydm.widgets import PyDMEmbeddedDisplay
from pydm.utilities import connection
from graph_display import graphDisplay

class TrackThread(QThread):

    # def __init__(self, injector, camera, cspad, stopper, pulse_picker, wave8, params):
    # devices are not connected, use 'fake' PVs instead
    def __init__(self, jt_input, jt_output, jt_fake):
        super().__init__()

        # self.injector = injector
        #self.camera = camera
        #self.cspad = cspad
        #self.stopper = stopper
        #self.pulse_picker = pulse_picker
        #self.wave8 = wave8
        #self.params = params

        # devices are not connected, use 'fake' PVs instead
        self.jt_input = jt_input
        self.jt_output = jt_output
        self.jt_fake = jt_fake

    def run(self):
        while not self.isInterruptionRequested():
            # check if stopper is in
            #if (jt_utils.get_stopper(self.stopper) == 1):
            if (self.jt_fake.stopper.get() == 1):
                # if stopper is in, stop jet tracking
                print('Stopper in - TRACKING STOPPED')
                self.requestInterruption()
                continue

            # check if pulse picker is closed
            #if (jt_utils.get_pulse_picker(self.pulse_picker) == 1):
            if (self.jt_fake.pulse_picker.get() == 1):
                # if pulse picker is closed, stop jet tracking
                print('Pulse picker closed - TRACKING STOPPED')
                self.requestInterruption()
                continue

            # check wave8
            # if (jt_utils.get_wave8(self.wave8) < self.params.thresh_w8):
            #if wave8 is below threshold, continue running jet tracking but do not move
            #print('Wave8 below threshold - NOT TRACKING')
            #sleep(2)
            #continue

            # OR check number of frames passed? used during testing w/ 'fake' PVs
            # get nframes timestamp
            t_nframe = self.jt_output.nframe.get()[1]
            if (self.jt_output.nframe.get()[0] < self.jt_input.nframe.get() * 0.8):
                # if too few frames passed, continue running jet tracking but do not move
                print('Too few frames passed - NOT TRACKING')
                sleep(2)
                continue

            # check CSPAD
            # make sure nframes (or wave8, if that is what is used) timestamp
            # matches with CSPAD timestamp
            if (t_nframe != self.jt_output.det.get()[1]):
                # if the timetamps do not match try again
                continue

            #if (jt_utils.get_cspad(self.cspad) < self.params.thresh_lo):
            # params IOC is down, hardcode threshold
            if (self.jt_output.det.get()[0] < 0.45):
                # if CSPAD is below lower threshold, move jet
                #if (not self.params.bypass_camera()):
                # params IOC is down, hardcode bypass
                if (not False):
                    # if camera is not bypassed, check if there is a jet and location of jet
                    try:
                        #jet_control._jet_calculate_step(self.camera, self.params)
                        # if jet is more than certain microns away from x-rays, move jet
                        # using camera feedback
                        #if (self.params.jet_x.get() > self.params.thresh_cam):
                        #jet_control._jet_move_step(self.injector, self.camera, self.params)
                        #sleep(1) # change to however long it takes for jet to move
                        #continue

                        # devices are not connected, print status message instead
                        print('Detector below lower threshold - MOVING JET')
                        sleep(1)  # change to however long it takes for jet to move
                        continue
                    except Exception:
                        # if jet is not detected, continue running jet tracking but do not move
                        print('Cannot find jet - NOT TRACKING')
                        sleep(2)
                        continue
            # if camera is bypassed or if jet is less than certain microns away from x-rays,
            # scan jet across x-rays to find new maximum
            #jet_control.scan(self.injector, self.cspad)
            #intensity = jt_utils.get_cspad(azav, self.params.radius.get(), gas_detect)
            #self.params.intensity.put(intensity)

            # devices are not connected, print status message instead
            print('Detector below lower threshold - SCANNING JET')
            sleep(1)  # change to however long it takes for jet to scan

            # if CSPAD still below upper threshold, stop jet tracking
            # if (get_cspad(self.cspad) < self.params.thresh_hi):
            # params IOC is down, hardcode threshold
            if (self.jt_output.det.get()[0] < 0.5):
                print('CSPAD below threshold - TRACKING STOPPED')
                self.requestInterruption()
                continue

            print('Running')
            print(self.jt_output.det.get())
            sleep(2)
    
class Counter(QObject):
    """
    Class intended to be used in a separate thread to generate numbers and send
    them to another thread.
    """

    params = pyqtSignal(list)
    stopped = pyqtSignal()

    def start(self):
        """
        Count from 0 to 99 and emit each value to the GUI thread to display.
        """
        values = [[0],[0]]
        print(values[0], values[1])
        for x in range(100):
            values[0].append(x)
            values[1].append((2*x))
            self.params.emit(values)
            time.sleep(0.5)
        self.stopped.emit()  

class thread(QThread):
    thread_data = pyqtSignal(list)
    def __init__(self, parent=None):
        super(QThread, self).__init__(parent)
        
        self.context_data = zmq.Context()
        self.socket_data = self.context_data.socket(zmq.SUB)
        self.socket_data.connect(''.join(['tcp://localhost:','8123']))
        self.socket_data.subscribe("")

    def run(self):
        while True:
            md = self.socket_data.recv_json(flags=0)
            msg = self.socket_data.recv(flags=0, copy=False,track=False)
            buf = memoryview(msg)
            data = np.frombuffer(buf, dtype=md['dtype'])
            data = np.ndarray.tolist(data.reshape(md['shape']))
            self.thread_data.emit(data)

class GraphicsView(QGraphicsView):

    def __init__(self, parent=None):

        super(GraphicsView, self).__init__(parent)

        self.setMouseTracking(True)


class GraphicsScene(QGraphicsScene):

    def __init__(self, parent=None):

        super(GraphicsScene, self).__init__(parent)
        #self.thread = thread()

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
    def setCameraStylesheet(self):
        #this will change based on the status given back
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

        #reference to PyDMApplication - this line is what makes it so that you can avoid 
        #having to define main() and instead pydm handles that for you - it is a subclass of QWidget
        self.app = QApplication.instance()

        #load data from file
        self.load_data()
        
        
        #assemble widgets
        self.setup_ui()

    def minimumSizeHint(self):
        
        return(QtCore.QSize(1000,600))
    
    def ui_filepath(self):

        #no Ui file is being used as of now
        return(None)
    
    def load_data(self):

        #this is responsible for opening the database and adding the information to self.data
        #https://slaclab.github.io/pydm-tutorial/action/python.html

        pass
    def setup_ui(self):
        #set default style sheet
        #self.setDefaultStyleSheet()
        
        #create layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        #give it a title
        self.lbl_title = Label("Jet Tracking")
        self.lbl_title.setTitleStylesheet()
        self._layout.addWidget(self.lbl_title)
        self._layout.addStretch(1)
        self.lbl_title.setMaximumHeight(35)

        #add a main layout for under the title which holds graphs and user controls
        self.layout_main = QHBoxLayout()
        self._layout.addLayout(self.layout_main)

        #####################################################################
        # make views/scenes to hold pydm graphs
        #####################################################################
        
        self.view_graph1 = pg.PlotWidget()
        self.view_graph2 = pg.PlotWidget()
        self.view_graph3 = pg.PlotWidget()
        #self.view_graph1 = GraphicsView()
        #self.view_graph2 = GraphicsView()
        #self.view_graph3 = GraphicsView()
        #self.scene_graph1 = GraphicsScene()
        #self.scene_graph2 = GraphicsScene()
        #self.scene_graph3 = GraphicsScene()
        #self.view_graph1.setScene(self.scene_graph1)
        #self.view_graph2.setScene(self.scene_graph2)
        #self.view_graph3.setScene(self.scene_graph3) 
        
        ######## setup layout ##########
        self.frame_graph = QFrame()
        self.frame_graph.setMinimumHeight(500)
        self.layout_graph = QVBoxLayout()
        self.frame_graph.setLayout(self.layout_graph)
        self.layout_graph.addWidget(self.view_graph1)
        self.layout_graph.addWidget(self.view_graph2)
        self.layout_graph.addWidget(self.view_graph3)
        ################################

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
        # make drop down menu for changing binning for sigma
        #####################################################################

        self.lbl_cbox_bins = Label("Sigma Bins")
        self.lbl_cbox_bins.setSubtitleStyleSheet()
        
        self.cbox_bins = ComboBox()

        #######setup layout#########
        self.frame_cbox_bins = QFrame()
        self.layout_cbox_bins = QHBoxLayout()
        self.frame_cbox_bins.setLayout(self.layout_cbox_bins)
        self.layout_usr_cntrl.addWidget(self.frame_cbox_bins)
        self.layout_cbox_bins.addWidget(self.lbl_cbox_bins)
        self.layout_cbox_bins.addWidget(self.cbox_bins)
        ############################

        ####################################################################
        # make buttons to choose between devices for checking if we have beam
        # currently either gas attenuator in the FEE or the Wave8
        ####################################################################

        self.lbl_init_initensity = Label("Initial beam Intensity RBV")
        self.lbl_init_initensity.setSubtitleStyleSheet()
        self.bttn_attenuator = PushButton("Gas Attenuator")
        self.bttn_wave8 = PushButton("Wave8")

        ####setup layout####
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

        self.lbl_camera = Label("Camera")
        self.lbl_camera.setSubtitleStyleSheet()
        self.lbl_camera_status = Label("No Tracing")
        self.lbl_camera_status.setCameraStylesheet()
        self.lbl_i0 = Label("Initial intensity (I0) RBV")
        self.lbl_i0.setSubtitleStyleSheet()
        self.lbl_i0_status = QLCDNumber(4)

        self.lbl_gdet_i0 = Label("I/I0 at detector")
        self.lbl_gdet_i0.setSubtitleStyleSheet()
        self.lbl_gdet_i0_status = QLCDNumber(4)

        ########setup layout###########
        self.layout_usr_cntrl.addWidget(self.lbl_status)

        self.frame_camera_status = QFrame()
        self.frame_camera_status.setLayout(QHBoxLayout())
        self.frame_camera_status.layout().addWidget(self.lbl_camera)
        self.frame_camera_status.layout().addWidget(self.lbl_camera_status)

        self.frame_i0 = QFrame()
        self.frame_i0.setLayout(QHBoxLayout())
        self.frame_i0.layout().addWidget(self.lbl_i0)
        self.frame_i0.layout().addWidget(self.lbl_i0_status)

        self.frame_gdet_i0 = QFrame()
        self.frame_gdet_i0.setLayout(QHBoxLayout())
        self.frame_gdet_i0.layout().addWidget(self.lbl_gdet_i0)
        self.frame_gdet_i0.layout().addWidget(self.lbl_gdet_i0_status)

        self.layout_usr_cntrl.addWidget(self.frame_camera_status)
        self.layout_usr_cntrl.addWidget(self.frame_i0)
        self.layout_usr_cntrl.addWidget(self.frame_gdet_i0)
        ###############################

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

        #########setup layout#########
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
        self.counterThread = QThread()
        self.counter = Counter()
        self.counter.moveToThread(self.counterThread)
        
        self.bttn_start.clicked.connect(self.startCounting)
        self.counter.params.connect(self.update_data)
        self.counter.stopped.connect(self.counterThread.quit)
        self.counterThread.started.connect(self.counter.start)
        
        #self.thread = thread()
        #self.thread.start()
        #self.graph_setup()
        #self.thread.thread_data.connect(self.update_data)

    def startCounting(self):
        if not self.counterThread.isRunning():
            self.counterThread.start()

    def setDefaultStyleSheet(self):

        ### This should be done with a json file
        
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

        self.gr = graphDisplay(self.view_graph1, self.view_graph2, self.view_graph3)
    
    def update_data(self, data):
        
        self.gr.plot_scroll(data)

# Jason Reily please stop helping us
# Arthur Brooks the Conservative heart

'''
class JetTrack(Display):

    def __init__(self, parent=None, args=None, macros=None):

        super(JetTrack, self).__init__(parent=parent,args=args, macros=macros)
        #def __init__(self, injector, camera, cspad, stopper, pulse_picker, wave8,
        #          params, macros, *args, **kwargs):
        #def __init__(self, jt_input, jt_output, jt_fake, macros, *args, **kwargs):
        #super().__init__(macros=macros, *args, **kwargs)

        #self.track_thread = TrackThread(injector, camera, cspad, stoppper,
        #                                pulse_picker, wave8, params)
        #self.track_thread = TrackThread(jt_input, jt_output, jt_fake)

        # connect GUI buttons to appropriate methods
        self.ui.calibrate_btn.clicked.connect(self.calibrate_clicked)
        self.ui.start_btn.clicked.connect(self.start_clicked)
        self.ui.stop_btn.clicked.connect(self.stop_clicked)

        self.ui.calibrate_btn.setEnabled(True)
        self.ui.start_btn.setEnabled(False)
        self.ui.stop_btn.setEnabled(False)

    def ui_filepath(self):
        return(path.join(path.dirname(path.realpath(__file__)), self.ui_filename()))

    def ui_filename(self):
        return 'jettracking.ui'

    def calibrate_clicked(self):
        self.ui.logger.write('Calibrating')
        self.ui.calibrate_btn.setEnabled(False)

        # call calibration method
        #jet_control.calibrate(injector, camera, cspad, params)

        self.ui.logger.write('Calibration complete - can now run jet tracking')
        self.ui.calibrate_btn.setEnabled(True)
        self.ui.start_btn.setEnabled(True)
        return

    def start_clicked(self):
        """Starts new jet tracking thread when start button is clicked."""
        self.ui.logger.write('Running jet tracking')
        self.ui.start_btn.setEnabled(False)
        self.ui.stop_btn.setEnabled(True)
        self.ui.calibrate_btn.setEnabled(False)
        self.track_thread.start()

    def stop_clicked(self):
        """Stops jet tracking when stop button is clicked."""
        self.track_thread.requestInterruption()
        self.ui.logger.write('Jet tracking stopped')
        self.ui.stop_btn.setEnabled(False)
        self.ui.start_btn.setEnabled(True)
        self.ui.calibrate_btn.setEnabled(True)
'''
