import json
import logging
import os
import threading
from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import yaml

log = logging.getLogger(__name__)
lock = threading.Lock()


class Context(object):

    def __init__(self, signals):
        self.signals = signals
        self.JT_LOC = ('/cds/group/pcds/epics-dev/espov/jet_tracking_all/'
                       'jet_tracking/')
        self.SD_LOC = '/reg/d/psdm/'
        self.SAVEFOLDER = '/cds/%sopr/experiments/%s/jet_tracking/output_data/'
        # default values. these are overwritten if a config file is used
        self.PV_DICT = {'diff': 'CXI:JTRK:REQ:DIFF_INTENSITY',
                        'i0': 'CXI:JTRK:REQ:I0',
                        'ratio': 'CXI:JTRK:REQ:RATIO',
                        'dropped': 'CXI:JTRK:REQ:DROPPED',
                        'camera': 'MFX:GIGE:05',
                        'motor': 'MFX:HRA:MMN:29'}
        #self.CFG_FILE = 'jt_configs/cxi_config.yml'
        self.HUTCH = 'cxi'
        self.EXPERIMENT = 'cxix53419'
        # end of defaults

        # parses config file
        self.parser = ArgumentParser()
        self.parser.add_argument('--cfg', type=str,
                                 default='jt_configs/cxi_config.yml')
        # parser.add_argument('--run', type=int, default=None)
        self.args = self.parser.parse_args()
        self.path = ('/cds/group/pcds/epics-dev/espov/jet_tracking_all/'
                     'jet_tracking/jt_configs/')
        self.JT_CFG = ''.join([self.JT_LOC, self.args.cfg])

        #with open(self.JT_CFG) as f:
        #    yml_dict = yaml.load(f, Loader=yaml.FullLoader)
        #    self.ipm_name = yml_dict['ipm']['name']
        #    self.motor = yml_dict['motor']['name']
        #    self.jet_cam_name = yml_dict['jet_cam']['name']
        #    self.jet_cam_axis = yml_dict['jet_cam']['axis']
        #    self.HUTCH = yml_dict['hutch']
        #    self.EXPERIMENT = os.environ.get('EXPERIMENT',
        #                                     yml_dict['experiment'])
        #    self.pv_map = yml_dict['pv_map']

        #if self.jet_cam_name == 'None' or self.jet_cam_name == 'none':
        #    self.jet_came_name = None

        #if self.motor == 'None' or self.motor == 'none':
        #    print('Please provide a motor PV in the config file')

        #self.pv_map['diff'] = self.pv_map.pop(1)
        #self.pv_map['i0'] = self.pv_map.pop(2)
        #self.pv_map['ratio'] = self.pv_map.pop(3)
        #self.pv_map['dropped'] = self.pv_map.pop(4)
        #self.pv_map['camera'] = self.jet_cam_name
        #self.pv_map['motor'] = self.motor
        #self.PV_DICT = self.pv_map

        self.live_data = True
        self.calibration_source = "calibration from results"
        self.num_cali = 50
        self.percent = 50
        self.refresh_rate = 5
        self.graph_ave_time = 2
        self.display_time = 10
        self.notification_time = 2
        self.calibrated = False
        self.calibration_values = {}
        self.naverage = self.graph_ave_time * self.refresh_rate  # number of points over the time wanted for averaging
        self.buffer_size = self.display_time * self.refresh_rate  # number of points over the graph time
        self.averaging_size = int(self.buffer_size / self.naverage)  # how many averages can fit within the time window
        self.x_axis = list(np.linspace(0, self.display_time, self.buffer_size))
        self.notification_tolerance = self.notification_time * self.refresh_rate
        self.ave_cycle = list(range(1, self.naverage + 1))
        self.x_cycle = list(range(0, self.buffer_size))
        self.ave_idx = list(range(0, self.averaging_size + 1))  # +1 for NaN value added at the end
        self.bad_scan_limit = 3

        # motor variables
        self.manual_motor = True
        self.high_limit = 0.1
        self.low_limit = -0.1
        self.step_size = 0.02
        self.position_tolerance = 0.001
        self.motor_averaging = 10
        self.algorithm = 'Ternary Search'
        self.motor_running = False
        self.motor_mode = ''
        self.live_motor = True
        self.motor_position = 0
        self.read_motor_position = 0
        self.isTracking = False
        self.live_data = True
        self.display_flag = None

        # used in simulator
        self.percent_dropped = 10
        self.peak_intensity = 10
        self.radius = 0.025
        self.jet_center = 0.03
        self.max = 10
        self.bg = 0.05
        self.cam_refresh_rate = 3

        self.generate_image = True
        self.jet_image_from_file = ""

    def update_live_graphing(self, live):
        self.live_data = live
        self.signals.changeRunLive.emit(self.live_data)
        self.signals.updateRunValues.emit(self.live_data)

    def update_calibration_source(self, cal_src):
        self.calibration_source = cal_src
        self.signals.changeCalibrationSource.emit(self.calibration_source)

    def update_num_cali(self, nc):
        self.num_cali = nc
        self.signals.changeNumberCalibration.emit(self.num_cali)

    def update_percent(self, p):
        """
        changes the percent threshold and emits a signal to the thread
        so that the range of allowed values and the graph will get updated
        """
        self.percent = p
        if self.calibrated:
            self.signals.changePercent.emit(self.percent)

    def update_graph_averaging(self, avg):
        """
        changes the number of points to average on the graph
        """
        if avg < self.display_time:
            self.graph_ave_time = avg
        else:
            self.graph_ave_time = self.display_time
        self.update_buffers_and_cycles("just average")

    def update_refresh_rate(self, rr):
        """
        changes the refresh rate of the graph
        """
        self.refresh_rate = int(rr)
        self.update_buffers_and_cycles("all")

    def update_display_time(self, dis_t):
        """
        updates the display time or the x-axis window
        """
        self.display_time = int(dis_t)
        self.update_buffers_and_cycles("all")

    def update_buffers_and_cycles(self, who):
        if who == "all":
            # if the display time, or refresh rate is changed then these should
            # also change:
            # 1. x_axis
            # 2. buffer_size
            # 3. averaging_size
            # 4. x_cycle
            # 5. ave_idx
            # 6. ave_cycle (the number of points to average has changed to
            #    achieve the same amount of time)
            # 7. naverage
            self.buffer_size = int(self.display_time * self.refresh_rate)
            self.naverage = int(self.graph_ave_time * self.refresh_rate)
            self.averaging_size = int(self.buffer_size / self.naverage)
            self.x_axis = list(np.linspace(0, self.display_time,
                               self.buffer_size))
            self.notification_tolerance = int(self.notification_time *
                                              self.refresh_rate)
            self.ave_cycle = list(range(1, self.naverage+1))
            self.x_cycle = list(range(0, self.buffer_size))
            self.ave_idx = list(range(0, self.averaging_size+1))
            self.signals.changeDisplayFlag.emit("all")

        if who == "just average":
            self.naverage = int(self.graph_ave_time * self.refresh_rate)
            self.averaging_size = int(self.buffer_size / self.naverage)
            self.ave_cycle = list(range(1, self.naverage+1))
            self.ave_idx = list(range(0, self.averaging_size+1))
            self.signals.changeDisplayFlag.emit("just average")

    def update_scan_limit(self, sl):
        self.bad_scan_limit = sl
        self.signals.changeScanLimit.emit(self.bad_scan_limit)

    def update_manual_motor(self, manual):
        """
        changes the motor between manual and automatic moving
        """
        self.manual_motor = manual
        self.signals.changeManual.emit(self.manual_motor)

    def update_limits(self, high, low):
        """
        updates the high and low limit for the motor and sends
        the values to the motor thread
        """
        self.high_limit = high
        self.low_limit = low
        self.signals.changeMotorLimits.emit(self.high_limit, self.low_limit)

    def update_step_size(self, ss):
        """
        updates the step size for the motor and sends
        the value to the motor thread
        """
        self.step_size = ss
        self.signals.changeStepSize.emit(self.step_size)

    def update_motor_averaging(self, v):
        """
        updates the amount of points to average for each motor move and
        sends the value to the motor thread
        """
        self.motor_averaging = v
        self.signals.changeMotorAveraging.emit(self.motor_averaging)

    def update_algorithm(self, a):
        """
        updates the algorithm used for motor moving and
        sends the string to the motor thread
        """
        self.algorithm = a

    def parse_config(self):  # Currently unused, saving for modularity
        with open(self.CFG_FILE) as f:
            yml_dict = yaml.load(f, Loader=yaml.FullLoader)
        return yml_dict
        # api_port = yml_dict['api_msg']['port']
        # det_map = yml_dict['det_map']
        # ipm_name = yml_dict['ipm']['name']
        # ipm_det = yml_dict['ipm']['det']
        # pv_map = yml_dict['pv_map']
        # jet_cam_name = yml_dict['jet_cam']['name']
        # jet_cam_axis = yml_dict['jet_cam']['axis']
        # sim = yml_dict['sim']
        # hutch = yml_dict['hutch']
        # exp = yml_dict['experiment']
        # run = yml_dict['run']

    def get_cal_results(self):
        results_dir = Path(f'/cds/home/opr/{self.HUTCH}opr/experiments/'
                           f'{self.EXPERIMENT}/jt_calib/')
        cal_files = list(results_dir.glob('jt_cal*'))
        cal_files.sort(key=os.path.getmtime)
        if cal_files:
            cal_file_path = cal_files[-1]
            with open(cal_file_path) as f:
                cal_results = json.load(f)
            return cal_results, cal_file_path
        else:
            return None, None

    def set_mode(self, mode):
        self.mode = mode
        self.signals.mode.emit(self.mode)

    def set_calibrated(self, c):
        self.calibrated = c

    def set_calibration_values(self, cal):
        self.calibration_values = cal

    def open_cam_connection(self):
        self.signals.connectCam.emit()

    def calibrate_image(self):
        if self.motor_running:
            self.signals.message.emit("the motor is currently running an algorithm. Try stopping motor first")
        else:
            self.update_motor_mode('calibrate')

    def update_motor_mode(self, mode):
        self.motor_mode = mode
        self.signals.motorMode.emit(self.motor_mode)
        if self.motor_mode == 'run':
            self.motor_running = True
        else:
            self.motor_running = False

    def update_tracking(self, tracking):
        self.isTracking = tracking
        self.signals.enableTracking.emit(self.isTracking)

    def connect_motor(self):
        self.signals.connectMotor.emit()

    def update_live_motor(self, live):
        self.live_motor = live
        self.signals.liveMotor.emit(live)

    def update_motor_position(self, p):
        self.motor_position = p
        self.signals.changeMotorPosition.emit(self.motor_position)

    def update_read_motor_position(self, p):
        self.read_motor_position = p
        self.signals.changeReadPosition.emit(self.read_motor_position)

    def update_motor_running(self, running):
        self.motor_running = running

    def update_peak_intensity(self, pi):
        self.peak_intensity = pi
        self.signals.changePeakIntensity.emit(self.peak_intensity)

    def update_jet_radius(self, r):
        self.radius = r
        self.signals.changeJetRadius.emit(self.radius)

    def update_jet_center(self, jc):
        self.jet_center = jc
        self.signals.changeJetCenter.emit(self.jet_center)

    def update_max_intensity(self, mi):
        self.max = mi
        self.signals.changeMaxIntensity.emit(self.max)

    def update_background(self, bgn):
        self.bg = bgn
        self.signals.changeBackground.emit(self.bg)

    def update_dropped_shots(self, ds):
        self.percent_dropped = ds
        self.signals.changeDroppedShots.emit(self.percent_dropped)

    def update_generate_image(self, gen_im):
        self.generate_image = gen_im

    def update_jet_image(self, im):
        self.jet_image_from_file = im
