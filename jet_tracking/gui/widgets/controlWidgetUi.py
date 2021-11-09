from PyQt5.QtWidgets import QVBoxLayout, QButtonGroup, QRadioButton, \
    QGridLayout, QHBoxLayout, QPushButton, QLCDNumber, \
    QFrame, QTextEdit, QSizePolicy

from gui.widgets.basicWidgets import CollapsibleBox, Label, LineEdit, ComboBox, QHLine


class Controls_Ui(object):

    def setupUi(self, obj):
        #####################################################################
        # set up user panel layout and give it a title
        #####################################################################
        obj.layout_usr_cntrl = QVBoxLayout(obj)
        obj.box_graph = CollapsibleBox("Graphing/Data collection")
        obj.layout_usr_cntrl.addWidget(obj.box_graph)

        #####################################################################
        # make radiobutton for selecting live or simulated data
        #####################################################################

        obj.bttngrp1 = QButtonGroup()

        obj.rdbttn_live = QRadioButton("live data")
        obj.rdbttn_sim = QRadioButton("simulated data")
        obj.rdbttn_live.setChecked(True)
        obj.bttngrp1.addButton(obj.rdbttn_live, id=1)
        obj.bttngrp1.addButton(obj.rdbttn_sim, id=0)
        obj.bttngrp1.setExclusive(True)

        obj.bttngrp3 = QButtonGroup()
        obj.rdbttn_cali_live = QRadioButton("calibration in GUI")
        obj.rdbttn_cali_live.setMinimumSize(10, 10)
        obj.rdbttn_cali = QRadioButton("calibration from results")
        obj.rdbttn_cali.setMinimumSize(10, 10)
        obj.rdbttn_cali.setChecked(True)
        obj.bttngrp3.addButton(obj.rdbttn_cali, id=0)
        obj.bttngrp3.addButton(obj.rdbttn_cali_live, id=1)
        obj.bttngrp3.setExclusive(True)

        # setup layout
        ##############
        obj.layout_graph = QVBoxLayout()
        obj.layout_allrdbttns = QGridLayout()
        obj.layout_allrdbttns.setColumnStretch(0, 6)
        obj.layout_allrdbttns.setColumnStretch(1, 1)
        obj.layout_allrdbttns.setRowStretch(1, 5)
        obj.layout_allrdbttns.addWidget(obj.rdbttn_live, 0, 0)
        obj.layout_allrdbttns.addWidget(obj.rdbttn_sim, 0, 1)
        obj.layout_allrdbttns.addWidget(obj.rdbttn_cali, 1, 0, 1, 2)
        obj.layout_allrdbttns.addWidget(obj.rdbttn_cali_live, 1, 1, 1, 2)
        obj.layout_allrdbttns.setRowMinimumHeight(0, 20)
        obj.layout_allrdbttns.setRowMinimumHeight(1, 30)
        obj.layout_graph.addLayout(obj.layout_allrdbttns)
        obj.layout_graph.addSpacing(5)

        #####################################################################
        # make input box for changing the percent of allowed values from the
        # mean and the number of points for averaging on the graph and the
        # refresh rate to update the points/graph and the amount of time being
        # viewed in the pyqtplot
        #####################################################################

        obj.lbl_percent = Label("Percent to Accept \n(1 - 99)")
        obj.le_percent = LineEdit("70")
        obj.le_percent.valRange(1, 100)
        obj.le_percent.setToolTip('Sets the percentage of I/I0 values that are accepted as normal based on a Gaussian distribution.\n Lower numbers are stricter and will trigger a scan more easily.')
        obj.lbl_notification_tol = Label("Notification Tolerance \n(10 - 300s)")
        obj.le_notification_tol = LineEdit('30')
        obj.le_notification_tol.valRange(10, 300)
        obj.le_notification_tol.setToolTip('Sets time delay before notifications trigger an action.')
        obj.lbl_ave_graph = Label('Averaging \n(1 - 30s)')
        obj.lbl_refresh_rate = Label('Refresh Rate \n(1 - 50Hz)')
        obj.le_ave_graph = LineEdit("5")
        obj.le_ave_graph.valRange(1, 30)
        obj.le_ave_graph.setToolTip('Sets averaging time for each point in the plots.')
        obj.le_refresh_rate = LineEdit("5")
        obj.le_refresh_rate.valRange(1, 50)
        obj.le_refresh_rate.setToolTip('Sets the refresh rate for the plots. \nHigh refresh rates may make the GUI run slowly.')
        obj.lbl_x_axis = Label("X-Axis Time View \n(10 - 120s)")
        obj.le_x_axis = LineEdit("60")
        obj.le_x_axis.valRange(10, 120)
        obj.le_x_axis.setToolTip('Sets the length of the time axis for the plots. \nThis parameter only refreshes after the plots have reached the current maximum time on the plots.')


        # setup layout
        ##############

        obj.layout_percent = QHBoxLayout()
        obj.layout_tol = QHBoxLayout()
        obj.layout_ave = QHBoxLayout()
        obj.layout_refresh = QHBoxLayout()
        obj.layout_x_axis = QHBoxLayout()
        obj.layout_percent.addWidget(obj.lbl_percent, 75)
        obj.layout_percent.addWidget(obj.le_percent)        
        obj.layout_tol.addWidget(obj.lbl_notification_tol, 75)
        obj.layout_tol.addWidget(obj.le_notification_tol)
        obj.layout_ave.addWidget(obj.lbl_ave_graph, 75)
        obj.layout_ave.addWidget(obj.le_ave_graph)
        obj.layout_refresh.addWidget(obj.lbl_refresh_rate, 75)
        obj.layout_refresh.addWidget(obj.le_refresh_rate)
        obj.layout_x_axis.addWidget(obj.lbl_x_axis, 75)
        obj.layout_x_axis.addWidget(obj.le_x_axis)
        obj.layout_graph.addLayout(obj.layout_percent)
        obj.layout_graph.addLayout(obj.layout_tol)
        obj.hline = QHLine()
        obj.layout_graph.addWidget(obj.hline)
        obj.layout_graph.addLayout(obj.layout_ave)
        obj.layout_graph.addLayout(obj.layout_refresh)
        obj.layout_graph.addLayout(obj.layout_x_axis)
        obj.box_graph.setContentLayout(obj.layout_graph)

        ###################################################################
        #  make section for editing motor parameters
        ###################################################################

        obj.box_motor = CollapsibleBox("Motor Controls")
        obj.layout_usr_cntrl.addWidget(obj.box_motor)

        obj.bttn_connect_motor = QPushButton("Connect Motor")

        obj.bttngrp2 = QButtonGroup()
        obj.rdbttn_manual = QRadioButton("manual \nmotor moving")
        obj.rdbttn_auto = QRadioButton("automated \nmotor moving")
        obj.rdbttn_manual.setChecked(True)
        obj.bttngrp2.addButton(obj.rdbttn_manual, id=1)
        obj.bttngrp2.addButton(obj.rdbttn_auto, id=0)
        obj.bttngrp2.setExclusive(True)

        obj.lbl_motor_hl = Label("High Limit (mm)")
        obj.lbl_motor_ll = Label("Low Limit (mm)")
        obj.lbl_motor_size = Label("Step Size (mm)")
        obj.lbl_motor_average = Label("Average Intensity")
        obj.lbl_algorithm = Label("Algorithm")

        obj.le_motor_hl = LineEdit("-0.1")
        obj.le_motor_hl.valRange(-100, 100)
        obj.le_motor_hl.setToolTip('End of search range.')

        obj.le_motor_ll = LineEdit("0.1")
        obj.le_motor_ll.valRange(-100, 100)
        obj.le_motor_ll.setToolTip('Beginning  of search range.')

        obj.le_size = LineEdit("0.02")
        obj.le_size.valRange(0, 100)
        obj.le_size.setToolTip('Move motor by this amount each step')

        obj.le_ave_motor = LineEdit("10")
        obj.le_ave_motor.valRange(1, 300)
        obj.le_ave_motor.setToolTip('???')

        obj.cbox_algorithm = ComboBox()
        obj.cbox_algorithm.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        obj.cbox_algorithm.addItem("Ternary Search")
        obj.cbox_algorithm.addItem("Basic Scan")
        obj.cbox_algorithm.addItem("Linear + Ternary")
        obj.cbox_algorithm.addItem("Dynamic Linear Scan")

        obj.bttn_search = QPushButton()
        obj.bttn_search.setText("Go Once")
        obj.bttn_search.setEnabled(True)
        obj.bttn_search.setToolTip('Runs the chosen search algorithm once and moves to the optimized motor position.')

        obj.bttn_tracking = QPushButton()
        obj.bttn_tracking.setText("Start Tracking")
        obj.bttn_tracking.setEnabled(False)
        obj.bttn_tracking.setToolTip('Enables tracking mode. \nA search will begin if scattering intensity drops below threshold.')

        obj.bttn_stop_motor = QPushButton()
        obj.bttn_stop_motor.setText("Stop Tracking")
        obj.bttn_stop_motor.setEnabled(False)
        obj.bttn_stop_motor.setToolTip('Disables tracking mode.')

        obj.lbl_tracking = Label("Tracking")
        obj.lbl_tracking.setSubtitleStyleSheet()
        obj.lbl_tracking_status = Label("False")
        obj.lbl_tracking_status.setStyleSheet(f"\
                background-color: red;")

        obj.layout_motor = QVBoxLayout()
        obj.layout_connect_motor = QHBoxLayout()
        obj.layout_motor_manual = QHBoxLayout()
        obj.layout_motor_input = QGridLayout()
        obj.layout_motor_bttns = QHBoxLayout()
        obj.layout_tracking = QHBoxLayout()
        obj.layout_motor.addLayout(obj.layout_connect_motor)
        obj.layout_motor.addLayout(obj.layout_motor_manual)
        obj.layout_motor.addLayout(obj.layout_motor_input)
        obj.layout_motor.addLayout(obj.layout_motor_bttns)
        obj.layout_motor.addWidget(obj.bttn_connect_motor)
        obj.layout_motor_manual.addWidget(obj.rdbttn_manual)
        obj.layout_motor_manual.addWidget(obj.rdbttn_auto)
        obj.layout_motor_input.addWidget(obj.lbl_motor_ll, 0, 0, 2, 1)
        obj.layout_motor_input.addWidget(obj.le_motor_ll, 0, 1, 2, 1)
        obj.layout_motor_input.addWidget(obj.lbl_motor_hl, 0, 2, 2, 1)
        obj.layout_motor_input.addWidget(obj.le_motor_hl, 0, 3, 2, 1)
        obj.layout_motor_input.addWidget(obj.lbl_motor_size, 3, 0, 2, 1)
        obj.layout_motor_input.addWidget(obj.le_size, 3, 1, 2, 1)
        obj.layout_motor_input.addWidget(obj.lbl_motor_average, 3, 2, 2, 1)
        obj.layout_motor_input.addWidget(obj.le_ave_motor, 3, 3, 2, 1)
        obj.layout_motor_input.addWidget(obj.lbl_algorithm, 5, 0, 2, 1)
        obj.layout_motor_input.addWidget(obj.cbox_algorithm, 5, 1, 2, 2)
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
        
        obj.lbl_motor = Label("Motor Position (mm)")
        obj.lbl_motor_status = QLCDNumber(7)

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

        obj.frame_motor = QFrame()
        obj.frame_motor.setLayout(QHBoxLayout())
        obj.frame_motor.layout().addWidget(obj.lbl_motor)
        obj.frame_motor.layout().addWidget(obj.lbl_motor_status)

        obj.layout_usr_cntrl.addWidget(obj.frame_monitor_status)
        obj.layout_usr_cntrl.addWidget(obj.frame_tracking_status)
        obj.layout_usr_cntrl.addWidget(obj.frame_i0)
        obj.layout_usr_cntrl.addWidget(obj.frame_diff_i0)
        
        obj.layout_usr_cntrl.addWidget(obj.frame_motor)
        
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
