from PyQt5.QtWidgets import (QButtonGroup, QComboBox, QFrame, QGridLayout,
                             QHBoxLayout, QLCDNumber, QPushButton,
                             QRadioButton, QSizePolicy, QTextEdit, QVBoxLayout)

from ..widgets.basicWidgets import CollapsibleBox, Label, LineEdit, QHLine


class Controls_Ui:

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

        obj.rdbttn_live = QRadioButton("Live data")
        obj.rdbttn_all_sim = QRadioButton("All simulated")
        obj.rdbttn_part_sim = QRadioButton("Sim data + Live motor/image")
        obj.rdbttn_live.setChecked(True)
        obj.bttngrp1.addButton(obj.rdbttn_live, id=1)
        obj.bttngrp1.addButton(obj.rdbttn_all_sim, id=0)
        obj.bttngrp1.addButton(obj.rdbttn_part_sim, id=2)
        obj.bttngrp1.setExclusive(True)

        obj.bttngrp3 = QButtonGroup()
        obj.rdbttn_cali_live = QRadioButton("calibration in GUI")
        obj.rdbttn_cali_live.setMinimumSize(15, 10)
        obj.rdbttn_cali = QRadioButton("calibration from results")
        obj.rdbttn_cali.setMinimumSize(10, 10)
        obj.rdbttn_cali.setChecked(True)
        obj.bttngrp3.addButton(obj.rdbttn_cali, id=0)
        obj.bttngrp3.addButton(obj.rdbttn_cali_live, id=1)
        obj.bttngrp3.setExclusive(True)

        obj.bttngrp4 = QButtonGroup()
        obj.rdbttn_cali_after = QRadioButton("calibrate after completed")
        obj.rdbttn_cali_after.setMinimumSize(10, 10)
        obj.rdbttn_keep_cali = QRadioButton("keep current calibration")
        obj.rdbttn_keep_cali.setMinimumSize(10, 10)
        obj.rdbttn_cali_after.setChecked(True)
        obj.bttngrp4.addButton(obj.rdbttn_cali_after, id=0)
        obj.bttngrp4.addButton(obj.rdbttn_keep_cali, id=1)
        obj.bttngrp4.setExclusive(True)

        # setup layout
        ##############
        obj.layout_graph = QVBoxLayout()
        obj.layout_live = QHBoxLayout()
        obj.layout_cali_live = QHBoxLayout()
        obj.layout_cali_after = QHBoxLayout()
        obj.layout_live.addWidget(obj.rdbttn_live)
        obj.layout_live.addWidget(obj.rdbttn_all_sim)
        obj.layout_live.addWidget(obj.rdbttn_part_sim)
        obj.layout_cali_live.addWidget(obj.rdbttn_cali)
        obj.layout_cali_live.addWidget(obj.rdbttn_cali_live)
        obj.layout_cali_after.addWidget(obj.rdbttn_cali_after)
        obj.layout_cali_after.addWidget(obj.rdbttn_keep_cali)
        obj.layout_graph.addLayout(obj.layout_live)
        obj.layout_graph.addLayout(obj.layout_cali_live)
        obj.layout_graph.addLayout(obj.layout_cali_after)
        obj.layout_graph.addSpacing(5)

        #####################################################################
        # make input box for changing the percent of allowed values from the
        # mean and the number of points for averaging on the graph and the
        # refresh rate to update the points/graph and the amount of time being
        # viewed in the pyqtplot
        #####################################################################

        obj.lbl_percent = Label("Percent to Accept \n(1 - 99)")
        obj.le_percent = LineEdit("70")
        obj.le_percent.valRange(1, 99)
        obj.le_percent.setToolTip('Sets the percentage of I/I0 values that are'
                                  ' accepted as normal based on a Gaussian '
                                  'distribution.\n Lower numbers are stricter '
                                  'and will trigger a scan more easily.')
        obj.lbl_notification_tol = Label("Notification Tolerance \n(10-300s)")
        obj.le_notification_tol = LineEdit('30')
        obj.le_notification_tol.valRange(10, 300)
        obj.le_notification_tol.setToolTip('Sets time delay before '
                                           'notifications trigger an action.')
        obj.lbl_ave_graph = Label('Averaging \n(1 - 30s)')
        obj.lbl_refresh_rate = Label('Refresh Rate \n(1 - 50Hz)')
        obj.le_ave_graph = LineEdit("5")
        obj.le_ave_graph.valRange(1, 30)
        obj.le_ave_graph.setToolTip('Sets averaging time for each point in the'
                                    ' plots.')
        obj.le_refresh_rate = LineEdit("5")
        obj.le_refresh_rate.valRange(1, 50)
        obj.le_refresh_rate.setToolTip('Sets the refresh rate for the plots. '
                                       '\nHigh refresh rates may make the GUI '
                                       'run slowly.')
        obj.lbl_x_axis = Label("X-Axis Time View \n(10 - 120s)")
        obj.le_x_axis = LineEdit("60")
        obj.le_x_axis.valRange(10, 120)
        obj.le_x_axis.setToolTip('Sets the length of the time axis for the '
                                 'plots. \nThis parameter only refreshes after'
                                 ' the plots have reached the current maximum '
                                 'time on the plots.')

        obj.lbl_number_calibration = Label("Number of calibration points "
                                           "\n(10 - 250)")
        obj.le_number_calibration = LineEdit("50")
        obj.le_number_calibration.valRange(10, 250)
        obj.le_number_calibration.setToolTip('Sets the number of points '
                                             'to use for averaging to find '
                                             'new calibration values')

        # setup layout
        ##############
        obj.layout_number_calibration = QHBoxLayout()
        obj.layout_percent = QHBoxLayout()
        obj.layout_tol = QHBoxLayout()
        obj.layout_ave = QHBoxLayout()
        obj.layout_refresh = QHBoxLayout()
        obj.layout_x_axis = QHBoxLayout()
        obj.layout_number_calibration.addWidget(obj.lbl_number_calibration)
        obj.layout_number_calibration.addWidget(obj.le_number_calibration)
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
        obj.hline1 = QHLine()
        obj.hline2 = QHLine()
        obj.layout_graph.addLayout(obj.layout_number_calibration)
        obj.layout_graph.addWidget(obj.hline1)
        obj.layout_graph.addLayout(obj.layout_percent)
        obj.layout_graph.addLayout(obj.layout_tol)
        obj.layout_graph.addWidget(obj.hline2)
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
        obj.lbl_bad_scan = Label("Bad Scan Limit")

        obj.lbl_motor_pos = Label("Motor Position (mm)")
        obj.le_motor_pos = LineEdit("0")

        obj.le_motor_hl = LineEdit("-0.1")
        obj.le_motor_hl.valRange(-100, 100)
        obj.le_motor_hl.setToolTip('End of search range.')

        obj.le_motor_ll = LineEdit("0.1")
        obj.le_motor_ll.valRange(-100, 100)
        obj.le_motor_ll.setToolTip('Beginning  of search range.')

        obj.le_size = LineEdit("0.02")
        obj.le_size.valRange(0, 100)
        obj.le_size.setToolTip('Move motor by this amount each step in basic '
                               'scans')

        obj.le_ave_motor = LineEdit("10")
        obj.le_ave_motor.valRange(1, 300)
        obj.le_ave_motor.setToolTip('Number of points to average before moving'
                                    ' motor')

        obj.le_bad_scan = LineEdit("3")
        obj.le_bad_scan.valRange(1, 10)
        obj.le_bad_scan.setToolTip('Number of bad scans that can be attempted'
                                   ' before automatically turning off tracking')

        obj.cbox_algorithm = QComboBox()
        obj.cbox_algorithm.setSizePolicy(QSizePolicy.Expanding,
                                         QSizePolicy.Preferred)
        obj.cbox_algorithm.addItem("Ternary Search")
        obj.cbox_algorithm.addItem("Basic Scan")
        obj.cbox_algorithm.addItem("Linear + Ternary")
        obj.cbox_algorithm.addItem("Dynamic Linear Scan")
        obj.cbox_algorithm.addItem("Course + fine")

        obj.le_tolerance = LineEdit("0.001")
        obj.le_tolerance.setToolTip('Tolerance for ternary search, stops when '
                                    'step size equals tolerance')
        obj.le_tolerance.valRange(0, 10)
        obj.lbl_tolerance = Label("Tolerance (mm)")

        obj.le_int_time = LineEdit("20")
        obj.le_int_time.setToolTip('Number of points per step during a scan')
        obj.le_int_time.valRange(1, 100)
        obj.lbl_int_time = Label("Step Points")

        obj.bttn_search = QPushButton()
        obj.bttn_search.setText("Go Once")
        obj.bttn_search.setEnabled(True)
        obj.bttn_search.setToolTip('Runs the chosen search algorithm once and '
                                   'moves to the optimized motor position.')

        obj.bttn_stop_current_scan = QPushButton()
        obj.bttn_stop_current_scan.setText("Stop Scan")
        obj.bttn_stop_current_scan.setEnabled(True)
        obj.bttn_stop_current_scan.setToolTip("Stops the current scan in its "
                                              "tracks!")

        obj.bttn_tracking = QPushButton()
        obj.bttn_tracking.setText("Start Tracking")
        obj.bttn_tracking.setEnabled(False)
        obj.bttn_tracking.setToolTip('Enables tracking mode. \nA search will '
                                     'begin if the scattering intensity drops '
                                     'below the threshold.')

        obj.bttn_stop_motor = QPushButton()
        obj.bttn_stop_motor.setText("Stop Motor")
        obj.bttn_stop_motor.setEnabled(True)
        obj.bttn_stop_motor.setToolTip('Disables tracking mode.')

        obj.lbl_tracking = Label("Tracking")
        obj.lbl_tracking.setSubtitleStyleSheet()
        obj.lbl_tracking_status = Label("False")
        obj.lbl_tracking_status.setStyleSheet("background-color: red;")

        obj.layout_motor = QVBoxLayout()
        obj.layout_connect_motor = QHBoxLayout()
        obj.layout_motor_manual = QHBoxLayout()
        obj.layout_motor_input = QGridLayout()
        obj.layout_scan_settings = QHBoxLayout()
        obj.layout_bad_scan = QHBoxLayout()
        obj.layout_motor_position = QHBoxLayout()
        obj.layout_motor_bttns = QHBoxLayout()
        obj.layout_single_scan = QHBoxLayout()
        obj.layout_tracking = QHBoxLayout()
        obj.hline3 = QHLine()
        obj.hline4 = QHLine()
        obj.layout_motor.addLayout(obj.layout_connect_motor)
        obj.layout_motor.addLayout(obj.layout_motor_manual)
        obj.layout_motor.addLayout(obj.layout_motor_input)
        obj.layout_motor.addLayout(obj.layout_scan_settings)
        obj.layout_motor.addLayout(obj.layout_bad_scan)
        obj.layout_motor.addWidget(obj.hline3)
        obj.layout_motor.addLayout(obj.layout_motor_position)
        obj.layout_motor.addWidget(obj.hline4)
        obj.layout_motor.addLayout(obj.layout_single_scan)
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
        obj.layout_scan_settings.addWidget(obj.lbl_tolerance)
        obj.layout_scan_settings.addWidget(obj.le_tolerance)
        obj.layout_scan_settings.addWidget(obj.lbl_int_time)
        obj.layout_scan_settings.addWidget(obj.le_int_time)
        obj.layout_bad_scan.addWidget(obj.lbl_bad_scan)
        obj.layout_bad_scan.addWidget(obj.le_bad_scan)
        obj.layout_motor_position.addWidget(obj.lbl_motor_pos)
        obj.layout_motor_position.addWidget(obj.le_motor_pos)
        obj.layout_single_scan.addWidget(obj.bttn_search)
        obj.layout_single_scan.addWidget(obj.bttn_stop_current_scan)
        obj.layout_motor_bttns.addWidget(obj.bttn_tracking)
        obj.layout_motor_bttns.addWidget(obj.bttn_stop_motor)
        obj.box_motor.setContentLayout(obj.layout_motor)

        #####################################################################
        # give a status area that displays values and current tracking
        # reliability based on various readouts
        #####################################################################

        obj.lbl_status = Label("Status")
        obj.lbl_status.setStyleSheet(
            "qproperty-alignment: AlignCenter;"
            "border: 1px solid #FF17365D;"
            "background-color: #FF17365D;"
            "font-size: 28px;"
        )

        obj.lbl_monitor = Label("Monitor")
        obj.lbl_monitor.setStyleSheet(
            "qproperty-alignment: AlignCenter;"
            "border: 1px solid #FF17365D;"
            "background-color: #FF17365D;"
        )
        obj.lbl_monitor_status = Label("Not Started")

        obj.lbl_tracking = Label("Tracking")
        obj.lbl_tracking.setStyleSheet(
            "qproperty-alignment: AlignCenter;"
            "border: 1px solid #FF17365D;"
            "background-color: #FF17365D;"
        )
        obj.lbl_tracking_status = Label("False")
        obj.lbl_tracking_status.setStyleSheet("background-color: red;")

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

        #######################################################################
        # text area for giving updates the user can see
        #######################################################################

        obj.text_area = QTextEdit("~~~read only information for user~~~")
        obj.text_area.setReadOnly(True)
        obj.layout_usr_cntrl.addWidget(obj.text_area)

        #######################################################################
        # main buttons!!!!
        #######################################################################

        obj.bttn_calibrate = QPushButton("Calibrate")
        obj.bttn_calibrate.setStyleSheet("\
            background-color: yellow;\
            font-size:28px;\
            ")
        obj.bttn_start = QPushButton("Start")
        obj.bttn_start.setStyleSheet("\
            background-color: green;\
            font-size:28px;\
            ")
        obj.bttn_stop = QPushButton("Stop")
        obj.bttn_stop.setStyleSheet("\
            background-color: red;\
            font-size:28px;\
            ")

        # setup layout
        ##############
        obj.frame_jjbttns = QFrame()
        obj.frame_jjbttns.setLayout(QHBoxLayout())
        obj.frame_jjbttns.layout().addWidget(obj.bttn_calibrate)
        obj.frame_jjbttns.layout().addWidget(obj.bttn_start)
        obj.frame_jjbttns.layout().addWidget(obj.bttn_stop)

        obj.layout_usr_cntrl.addWidget(obj.frame_jjbttns)
