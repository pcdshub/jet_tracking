import logging
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
                            QGraphicsView, QGraphicsScene, 
                            QComboBox, QPushButton, QLineEdit,
                            QLabel, QFrame,QVBoxLayout, QHBoxLayout,
                            QWidget, QGridLayout, QTextEdit,
                            QButtonGroup, QRadioButton, QLCDNumber, 
                            QAbstractScrollArea, QSizePolicy, QToolButton,
                            QScrollArea
                            )
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import (
                         pyqtSignal, Qt, QParallelAnimationGroup, 
                         QPropertyAnimation, QAbstractAnimation, QThread
                         )
from jetgraphing import ScrollingTimeWidget, graph_setup, add_calibration_graph
from datastream import StatusThread, MotorThread
import pyqtgraph as pg
import collections

logging = logging.getLogger('pydm')
logging.setLevel('CRITICAL')

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

class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)
        self.toggle_button = QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton {border: none;\
                border: 1px solid #FF17365D;\
                border-top-left-radius: 15px;\
                border-top-right-radius: 15px;\
                background-color: #FF17365D;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                max-height: 30px;\
                font-size: 14px;\
            }\
            QToolButton:hover {\
                background-color: lightgreen;\
                color: black;\
            }")
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QParallelAnimationGroup(self)
        
        self.content_area = QScrollArea(
            maximumHeight=0, minimumHeight=0
        ) 
        self.content_area.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            Qt.DownArrow if not checked else Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QAbstractAnimation.Forward
            if not checked
            else QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def clear_layout(self, layout):
        try:
            for i in reversed(range(layout.count())):
                widgetToRemove = layout.itemAt(i).widget()
                layout.removeWidget(widgetToRemove)
                widgetToRemove.setPArent(None)
        except AttributeError:
            pass

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        self.clear_layout(lay)
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)
            
        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


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


class Graphs_Ui(object):

    def setupUi(self, obj):
        """
        used to setup the layout and initialize graphs
        """

        ################################
        # setup layout
        obj.layout = QVBoxLayout()
        obj.setLayout(self.layout)
        #obj.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        ################################

        obj.ratio_graph = ScrollingTimeWidget(self.signals)
        #obj.ratio_graph.setSizeHint(300, 300)
        #obj.ratio_graph.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred) 
        obj.i0_graph = ScrollingTimeWidget(self.signals)
        #obj.i0_graph.setMaximumHeight(300)
        obj.diff_graph = ScrollingTimeWidget(self.signals)
        #obj.diff_graph.setMaximumHeight(300)
        graph_setup(obj.ratio_graph, "Intensity Ratio", f"I/I\N{SUBSCRIPT ZERO}", \
                        pg.mkPen(width=5, color='r'))
        graph_setup(obj.i0_graph, "Initial Intensity", f"I\N{SUBSCRIPT ZERO}", \
                        pg.mkPen(width=5, color='b'))
        graph_setup(obj.diff_graph, "Intensity at the Detector", "Diffraction Intensity", \
                        pg.mkPen(width=5, color='g'))
        obj.i0_graph.setXLink(obj.ratio_graph)
        obj.diff_graph.setXLink(obj.ratio_graph)
        obj.layout.addWidget(obj.ratio_graph)
        obj.layout.addWidget(obj.i0_graph)
        obj.layout.addWidget(obj.diff_graph)

class GraphsWidget(QFrame, Graphs_Ui):
    def __init__(self, context, signals):
        super(GraphsWidget, self).__init__()

        self.signals = signals
        self.context = context
        self.calibrated = False
        self.calibration_values = {}
        self.setupUi(self)
        self.signals.buffers.connect(self.plot_data)
        self.signals.avevalues.connect(self.plot_ave_data)
        self.signals.calibration_value.connect(self.calibrate)

    def calibrate(self, cal):
        self.calibration_values = cal
        if self.calibrated:
            self.refresh_plots()
        self.calibrated = True

    def refresh_plots(self):
        self.ratio_graph.refreshCalibrationPlots()
        self.i0_graph.refreshCalibrationPlots()
        self.diff_graph.refreshCalibrationPlots()
        #add_calibration_plots(self.ratio_graph)
        #add_calibration_plots(self.i0_graph)
        #add_calibration_graph(self.diff_graph)


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




class Controls_Ui(object):

    def setupUi(self, obj):
        #####################################################################
        # set up user panel layout and give it a title
        #####################################################################
        obj.layout_usr_cntrl = QVBoxLayout(obj)

        obj.box_graph = CollapsibleBox("Graphing/Data collection")

        #obj.lbl_usr_cntrl = Label("Graphing stuffff")
        #obj.lbl_usr_cntrl.setTitleStylesheet()
        #obj.lbl_usr_cntrl.setMaximumHeight(35)
        #obj.layout_usr_cntrl.addWidget(obj.lbl_usr_cntrl)

        obj.layout_usr_cntrl.addWidget(obj.box_graph)
        #####################################################################
        # make radiobutton for selecting live or simulated data
        #####################################################################

        obj.bttngrp1 = QButtonGroup()

        obj.rdbttn_live = QRadioButton("live data")  # .setChecked(True)
        obj.rdbttn_sim = QRadioButton("simulated data")  # .setChecked(False)
        obj.rdbttn_live.setChecked(True)
        obj.bttngrp1.addButton(obj.rdbttn_live, id=1)
        obj.bttngrp1.addButton(obj.rdbttn_sim, id=0)
        obj.bttngrp1.setExclusive(True)  # allows only one button to be selected at a time
 
        obj.bttngrp3 = QButtonGroup()
        obj.rdbttn_cali_live = QRadioButton("calibration in GUI")
        obj.rdbttn_cali = QRadioButton("calibration from results")
        obj.rdbttn_cali.setChecked(True)
        obj.bttngrp3.addButton(obj.rdbttn_cali, id=0)
        obj.bttngrp3.addButton(obj.rdbttn_cali_live, id=1)
        obj.bttngrp3.setExclusive(True)

        # setup layout
        ##############
        obj.layout_graph = QVBoxLayout()
        obj.layout_allrdbttns = QGridLayout()
        obj.layout_allrdbttns.setColumnStretch(0, 1)
        obj.layout_allrdbttns.setColumnStretch(1, 1)
        obj.layout_allrdbttns.setColumnStretch(2, 1)
        obj.layout_allrdbttns.addWidget(obj.rdbttn_live, 0, 0)
        obj.layout_allrdbttns.addWidget(obj.rdbttn_sim, 0, 1)
        obj.layout_allrdbttns.addWidget(obj.rdbttn_cali, 1, 0)
        obj.layout_allrdbttns.addWidget(obj.rdbttn_cali_live, 1, 1)  
        obj.layout_graph.addLayout(obj.layout_allrdbttns)

        #####################################################################
        # make input box for changing the percent of allowed values from the
        # mean and the number of points for averaging on the graph and the 
        # refresh rate to update the points/graph
        #####################################################################

        obj.lbl_percent = Label("Percent \n(1 - 100)")
        obj.le_percent = LineEdit("70")
        obj.le_percent.valRange(1, 100)
        
        obj.lbl_ave_graph = Label('Averaging (graph) \n(5 - 300)')
        obj.lbl_refresh_rate = Label('Refresh Rate \n(2 - 300)')
        obj.le_ave_graph = LineEdit("50")
        obj.le_ave_graph.valRange(5, 300)
        obj.le_refresh_rate = LineEdit("50")
        obj.le_refresh_rate.valRange(2, 300)

        # setup layout
        ##############
        #obj.frame_samp = QFrame()
        obj.layout_samp = QHBoxLayout()
        #obj.frame_samp.setLayout(obj.layout_samp)
        #obj.layout_usr_cntrl.addWidget(obj.frame_samp)
        obj.layout_samp.addWidget(obj.lbl_percent)
        obj.layout_samp.addWidget(obj.le_percent)
        obj.layout_samp.addWidget(obj.lbl_ave_graph)
        obj.layout_samp.addWidget(obj.le_ave_graph)
        obj.layout_samp.addWidget(obj.lbl_refresh_rate)
        obj.layout_samp.addWidget(obj.le_refresh_rate)
        obj.layout_graph.addLayout(obj.layout_samp)
        obj.box_graph.setContentLayout(obj.layout_graph)

        ###################################################################
        #  make section for editing motor parameters
        ###################################################################
        
        obj.box_motor = CollapsibleBox("Motor Controls")
        #obj.lbl_motor = Label("Motor Parameters (microns)")
        #obj.lbl_motor.setTitleStylesheet()
        obj.layout_usr_cntrl.addWidget(obj.box_motor)

        obj.bttngrp2 = QButtonGroup()
        obj.rdbttn_manual = QRadioButton("manual motor moving")  # .setChecked(True)
        obj.rdbttn_auto = QRadioButton("automated motor moving")  # .setChecked(False)
        obj.rdbttn_manual.setChecked(True)
        obj.bttngrp2.addButton(obj.rdbttn_manual, id= 1)
        obj.bttngrp2.addButton(obj.rdbttn_auto, id = 0)
        obj.bttngrp2.setExclusive(True)  # allows only one button to be selected at a time

        obj.lbl_motor_hl = Label("High Limit")
        obj.lbl_motor_ll = Label("Low Limit")
        obj.lbl_motor_size = Label("Step Size")
        obj.lbl_motor_average = Label("Average Intensity")
        obj.lbl_algorithm = Label("Algorithm")        

        obj.le_motor_hl = LineEdit("50")
        obj.le_motor_hl.valRange(-100, 100)

        obj.le_motor_ll = LineEdit("-50")
        obj.le_motor_ll.valRange(-100, 100)

        obj.le_size = LineEdit(".5")
        obj.le_size.valRange(0, 100)

        obj.le_ave_motor = LineEdit("10")
        obj.le_ave_motor.valRange(1, 300)

        obj.cbox_algorithm = ComboBox()
        obj.cbox_algorithm.addItem("Ternary Search")
        obj.cbox_algorithm.addItem("Full Scan")

        obj.bttn_search = QPushButton()
        obj.bttn_search.setText("Search")
        obj.bttn_search.setEnabled(False) 

        obj.bttn_tracking = QPushButton()
        obj.bttn_tracking.setText("Track")
        obj.bttn_tracking.setEnabled(False)

        obj.bttn_stop_motor = QPushButton()
        obj.bttn_stop_motor.setText("Stop Tracking")
        obj.bttn_stop_motor.setEnabled(False)

        obj.lbl_tracking = Label("Tracking")
        obj.lbl_tracking.setSubtitleStyleSheet()
        obj.lbl_tracking_status = Label("False")
        obj.lbl_tracking_status.setStyleSheet(f"\
                background-color: red;")

        #obj.frame_motor = QFrame()
        obj.layout_motor = QVBoxLayout()
        obj.layout_motor_manual = QHBoxLayout()
        obj.layout_motor_input = QGridLayout()
        obj.layout_motor_bttns = QHBoxLayout()
        obj.layout_tracking = QHBoxLayout()
        obj.layout_motor.addLayout(obj.layout_motor_manual)
        obj.layout_motor.addLayout(obj.layout_motor_input)
        obj.layout_motor.addLayout(obj.layout_motor_bttns)
        #obj.frame_motor.setLayout(obj.layout_motor)
        #obj.layout_usr_cntrl.addWidget(obj.frame_motor)
        obj.layout_motor_manual.addWidget(obj.rdbttn_manual)
        obj.layout_motor_manual.addWidget(obj.rdbttn_auto)
        obj.layout_motor_input.addWidget(obj.lbl_motor_ll, 0, 0)
        obj.layout_motor_input.addWidget(obj.le_motor_ll, 0, 1)
        obj.layout_motor_input.addWidget(obj.lbl_motor_hl, 0, 2)
        obj.layout_motor_input.addWidget(obj.le_motor_hl, 0, 3)
        obj.layout_motor_input.addWidget(obj.lbl_motor_size, 1, 0)
        obj.layout_motor_input.addWidget(obj.le_size, 1, 1)
        obj.layout_motor_input.addWidget(obj.lbl_motor_average, 1, 2)
        obj.layout_motor_input.addWidget(obj.le_ave_motor, 1, 3)
        obj.layout_motor_input.addWidget(obj.lbl_algorithm, 2, 0)
        obj.layout_motor_input.addWidget(obj.cbox_algorithm, 2, 1)
        obj.layout_motor_bttns.addWidget(obj.bttn_search)
        obj.layout_motor_bttns.addWidget(obj.bttn_tracking)
        obj.layout_motor_bttns.addWidget(obj.bttn_stop_motor)
        obj.box_motor.setContentLayout(obj.layout_motor)

        #####################################################################
        # give a status area that displays values and current tracking
        # reliability based on various readouts
        #####################################################################

        obj.lbl_status = Label("Status")
        obj.lbl_status.setTitleStylesheet()

        obj.lbl_monitor = Label("Monitor")
        obj.lbl_monitor.setSubtitleStyleSheet()
        obj.lbl_monitor_status = Label("Not Started")

        obj.lbl_tracking = Label("Tracking")
        obj.lbl_tracking.setSubtitleStyleSheet()
        obj.lbl_tracking_status = Label("False")
        obj.lbl_tracking_status.setStyleSheet(f"\
                background-color: red;")

        obj.lbl_i0 = Label("Mean Initial intensity (I0)")
        obj.lbl_i0_status = QLCDNumber(7)

        obj.lbl_diff_i0 = Label("Mean I/I0")
        obj.lbl_diff_status = QLCDNumber(7)

        # setup layout
        ##############
        obj.layout_usr_cntrl.addWidget(obj.lbl_status)

        obj.frame_monitor_status = QFrame()
        obj.frame_monitor_status.setLayout(QHBoxLayout())
        obj.frame_monitor_status.layout().addWidget(obj.lbl_monitor)
        obj.frame_monitor_status.layout().addWidget(obj.lbl_monitor_status)

        obj.frame_tracking_status = QFrame()
        obj.frame_tracking_status.setLayout(QHBoxLayout())
        obj.frame_tracking_status.layout().addWidget(obj.lbl_tracking)
        obj.frame_tracking_status.layout().addWidget(obj.lbl_tracking_status)

        obj.frame_i0 = QFrame()
        obj.frame_i0.setLayout(QHBoxLayout())
        obj.frame_i0.layout().addWidget(obj.lbl_i0)
        obj.frame_i0.layout().addWidget(obj.lbl_i0_status)

        obj.frame_diff_i0 = QFrame()
        obj.frame_diff_i0.setLayout(QHBoxLayout())
        obj.frame_diff_i0.layout().addWidget(obj.lbl_diff_i0)
        obj.frame_diff_i0.layout().addWidget(obj.lbl_diff_status)

        obj.layout_usr_cntrl.addWidget(obj.frame_monitor_status)
        obj.layout_usr_cntrl.addWidget(obj.frame_tracking_status)
        obj.layout_usr_cntrl.addWidget(obj.frame_i0)
        obj.layout_usr_cntrl.addWidget(obj.frame_diff_i0)
        ###############################

        ########################################################################
        # text area for giving updates the user can see
        ########################################################################

        obj.text_area = QTextEdit("~~~read only information for user~~~")
        obj.text_area.setReadOnly(True)
        obj.layout_usr_cntrl.addWidget(obj.text_area)

        #########################################################################
        # main buttons!!!!
        #########################################################################

        obj.bttn_calibrate = QPushButton("Calibrate")
        obj.bttn_calibrate.setStyleSheet("\
            background-color: yellow;\
            font-size:12px;\
            ")
        obj.bttn_start = QPushButton("Start")
        obj.bttn_start.setStyleSheet("\
            background-color: green;\
            font-size:12px;\
            ")
        obj.bttn_stop = QPushButton("Stop")
        obj.bttn_stop.setStyleSheet("\
            background-color: red;\
            font-size:12px;\
            ")

        # setup layout
        ##############
        obj.frame_jjbttns = QFrame()
        obj.frame_jjbttns.setLayout(QHBoxLayout())
        obj.frame_jjbttns.layout().addWidget(obj.bttn_calibrate)
        obj.frame_jjbttns.layout().addWidget(obj.bttn_start)
        obj.frame_jjbttns.layout().addWidget(obj.bttn_stop)

        obj.layout_usr_cntrl.addWidget(obj.frame_jjbttns)
        ##############################




class ControlsWidget(QFrame, Controls_Ui):
    def __init__(self, context, signals):
        super(ControlsWidget, self).__init__()
        self.signals = signals
        self.context = context
        self.setupUi(self)
        self.calibrated = False
        self.thread_options = {}
        #  keys:
        #  live graphing
        #  calibration source
        #  percent
        #  averaging
        #  sampling rate
        #  manual motor
        self.worker_motor = None
        self.motor_options = {}
        #  keys:
        #  high limit
        #  low limit
        #  step size
        #  averaging
        #  scanning algorithm
        self.worker_status = None
        print("Main Thread: %d" % QThread.currentThreadId()) 

        ##################################################
        #  tracking values
        ##################################################
        
        self.thread_options['live graphing'] = self.bttngrp1.checkedId()
        self.thread_options['calibration source'] = self.bttngrp3.checkedId()
        self.thread_options['percent'] = float(self.le_percent.text())
        self.thread_options['averaging'] = float(self.le_ave_graph.text())
        self.thread_options['sampling rate'] = float(self.le_refresh_rate.text())
        self.thread_options['manual motor'] = self.bttngrp2.checkedId()

        self.motor_options['high limit'] = float(self.le_motor_hl.text())
        self.motor_options['low limit'] = float(self.le_motor_ll.text())
        self.motor_options['step size'] = float(self.le_size.text())
        self.motor_options['averaging'] = float(self.le_ave_motor.text())
        self.motor_options['scanning algorithm'] = self.cbox_algorithm.currentIndex()

        self._start()
       ###################################################

    def _start(self):
        self.worker_status = StatusThread(self.context, self.signals)
        self.worker_motor = MotorThread(self.context, self.signals)

        self.le_percent.checkVal.connect(self.update_percent)
        self.le_refresh_rate.checkVal.connect(self.update_refresh_rate)
        self.le_ave_graph.checkVal.connect(self.update_nsamp)
        self.le_motor_ll.checkVal.connect(self.update_limits)
        self.le_motor_hl.checkVal.connect(self.update_limits)
        self.le_size.checkVal.connect(self.update_tol)
        self.bttngrp1.buttonClicked.connect(self.checkBttn)
        self.bttngrp2.buttonClicked.connect(self.checkBttn)
        self.bttngrp3.buttonClicked.connect(self.checkBttn)

        self.bttn_search.clicked.connect(self._start_motor)
        self.bttn_tracking.clicked.connect(self._enable_tracking)
        self.bttn_stop_motor.clicked.connect(self._stop_motor)

        self.signals.status.connect(self.update_monitor_status)

        self.signals.wake.connect(self._start_motor)
        self.signals.sleep.connect(self._stop_motor)
        self.signals.message.connect(self.receive_message)

        self.bttn_stop.clicked.connect(self._stop)
        self.bttn_calibrate.clicked.connect(self._calibrate)
        self.signals.calibration_value.connect(self.update_calibration)
        self.signals.threadOp.emit(self.thread_options)
        self.bttn_start.clicked.connect(self.worker_status.start)

    def _stop(self):
        if self.worker_motor.isRunning():
            self.worker_motor.requestInterruption()
            self.worker_motor.wait()
        if self.worker_status.isRunning():
            self.worker_status.requestInterruption()
            self.worker_status.wait()

    def _calibrate(self):
        if not self.worker_status.isRunning():
            self.text_area.append("You are not running so there's \
                  nothing to calibrate.. hit start first")
        else:
            self.signals.threadOp.emit(self.thread_options)
            self.signals.mode.emit("calibrate")

    def _enable_tracking(self):
        self.update_tracking_status("enabled", green)
        self.isTracking = True
        self._start_motor()

    def _start_motor(self):
        if not self.worker_motor.isRunning():
            if self.worker_status.isRunning():
                self.signals.motorOp.emit(self.motor_options)
                self.signals.mode.emit("correcting")
                self.worker_motor.start()
            else:
                self.text_area.append("there's nothing to scan!")
        else:
            if self.worker_motor.isInterruptionRequested():
                self.signals.motorOp.emit(self.motor_options)
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
        """
        this function is called when the calibration button is ran, and a successful calibration 
        is done from the StatusThread. It gets the dictionary of calibration values from the thread
        and sets the calibration values. It also updates the display. It checks if the calibration has 
        been ran before. If it has, then it clears the calibration plots and then resets them.
        """
        
        self.calibration_values = cal
        self.lbl_i0_status.display(self.calibration_values['i0']['mean'])
        self.lbl_diff_status.display(self.calibration_values['diff']['mean'])
        self.calibrated = True 

    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            widgetToRemove = layout.itemAt(i).widget()
            layout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

    def update_tracking_status(self, status, color):
        self.lbl_tracking_status.setText(status)
        self.lbl_tracking_status.setStyleSheet(f"\
                background-color: {color};")
        self.signals.enable_tracking.emit(self.isTracking)

    def update_monitor_status(self, status, color):
        self.lbl_monitor_status.setText(status)
        self.lbl_monitor_status.setStyleSheet(f"\
                background-color: {color};")

    def cleanup_correction(self):
        self.worker_motor = None

    def thread_running(self, t):
        if t != None: return(True)
        else: return(False)

    def receive_status(self, status):
        if status == 'outside':
           if self.correction_thread is None:
               #avoid issues with fluctuations and multiple corrections
               self.correction_thread = correctionThread()
               self.correction_thread.finished.connect(self.cleanup_correction)
               self.correction_thread.start()

    def update_percent(self, percent):
        self.thread_options['percent'] = percent
        if self.thread_running(self.worker_status):
            self.signals.threadOp.emit(self.thread_options)
        if self.calibrated:
            self.signals.mode.emit('calibrate')

    def update_nsamp(self, nsamp):
        self.thread_options['average'] = nsamp
        if self.thread_running(self.worker_status):
            self.signals.threadOp.emit(self.thread_options)

    def update_refresh_rate(self, rrate):
        self.thread_options['sampling rate'] = rrate
        if self.thread_running(self.worker_status):
            self.signals.threadOp.emit(self.thread_options)

    def update_limits(self, limit):
        self.motor_options['high limit'] = float(self.le_motor_hl.text())
        self.motor_options['low limit'] = float(self.le_motor_ll.text())
        if self.thread_running(self.worker_status):
            self.signals.motorOp.emit(self.motor_options)

    def update_tol(self, tol):
        self.motor_options['step size'] = float(tol)
        if self.thread_running(self.worker_motor):
            self.signals.motorOp.emit(self.motor_options)

    def update_motor_avg(self, avg):
        self.motor_options['averaging'] = float(avg)
        if self.thread_running(self.worker_motor):
            self.signals.motorOp.emit(self.motor_options)

    def update_algorithm(self, alg): 
        self.motor_options['scanning algorithm'] = self.cbox_algorithm.currentIndex()
        if self.thread_running(self.worker_motor):
            self.signals.motorOp.emit(self.motor_options)

    def receive_message(self, message):
        self.text_area.append(message)

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

