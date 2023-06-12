import json
import logging
import os
from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import yaml

log = logging.getLogger("jet_tracker")


class Context(object):
    """
    The Context class represents the context or environment in which the application operates.
    It stores various settings, configurations, and data related to the application's functionality.

    Attributes:
        signals (object): Object containing different signals emitted by the context.
        JT_LOC (str): Jet tracking location path.
        SD_LOC (str): PSDM location path.
        SAVEFOLDER (str): Folder path for saving output data.
        PV_DICT (dict): Dictionary containing PV (Process Variable) mappings.
        HUTCH (str): Hutch name.
        EXPERIMENT (str): Experiment name.
        parser (ArgumentParser): Argument parser for command line arguments.
        args (Namespace): Namespace object containing parsed command line arguments.
        path (str): Path for jet tracking configurations.
        JT_CFG (str): Jet tracking configuration file path.
        live_data (bool): Flag indicating whether live data is enabled.
        calibration_source (str): Source of calibration data.
        num_cali (int): Number of calibrations to perform.
        percent (int): Percentage threshold for data analysis.
        refresh_rate (int): Refresh rate for graph updates.
        graph_ave_time (int): Time window for graph averaging.
        display_time (int): Display time or x-axis window size.
        notification_time (int): Time duration for notifications.
        calibrated (bool): Flag indicating if calibration has been performed.
        calibration_values (dict): Dictionary containing calibration values.
        naverage (int): Number of points for averaging.
        num_points (int): Number of points for graph display.
        averaging_size (int): Size of averaging for the time window.
        x_axis (list): List of x-axis values for graph display.
        notification_tolerance (int): Tolerance for notification time.
        ave_cycle (list): List of indices for averaging cycle.
        x_cycle (list): List of indices for x-axis cycle.
        ave_idx (list): List of indices for averaging size.
        bad_scan_limit (int): Limit for bad scans.
        manual_motor (bool): Flag indicating manual control of motor.
        high_limit (float): High limit for motor position.
        low_limit (float): Low limit for motor position.
        step_size (float): Step size for motor movement.
        position_tolerance (float): Tolerance for motor position.
        motor_averaging (int): Number of points to average for motor movement.
        algorithm (str): Algorithm used for motor movement.
        motor_mode (str): Mode of the motor.
        live_motor (bool): Flag indicating if live motor data is enabled.
        motor_position (float): Current motor position.
        read_motor_position (float): Motor position read from the motor thread.
        display_flag (None or str): Flag indicating the display state.
        percent_dropped (int): Percentage of dropped shots.
        peak_intensity (int): Peak intensity value.
        radius (float): Jet radius value.
        jet_center (float): Jet center value.
        max (int): Maximum intensity value.
        bg (float): Background value.
        cam_refresh_rate (int): Refresh rate for camera updates.
        image_calibration_steps (list): List of image calibration steps.
        image_calibration_positions (list): List of image calibration positions.
        contours (list): List of contours.
        best_fit_line (list): List of points for best fit line.
        best_fit_line_plus (list): List of points for best fit line (positive side).
        best_fit_line_minus (list): List of points for best fit line (negative side).
        com (list): List of center of mass (COM) points.
        find_com_bool (bool): bool for whether to find and plot the COM and fitting information on the image
        dilate (int): number of iterations for dilation morphology operation
        erode (int): number of iterations for erode morphology operation
        open_operation (int): size of kernel for open morphology operation
        close_operation (int): size of kernel for close morphology operation
        brightness (int): brightness morphology operation
        contrast (int): contrast morphology operation
        blur (int): sigmax and sigmay for blur morphology operation
        threshold (int): threshold cutoff for thresholding morphology operation
        """
    def __init__(self, signals):
        log.debug("Supplying Thread information from init of Context")
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
                        'camera': 'XCS:GIGE:LJ2',
                        'motor': 'XCS:LJH:JET:Y'}
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
        self.num_points = self.display_time * self.refresh_rate  # number of points over the graph time
        self.averaging_size = int(self.num_points / self.naverage)  # how many averages can fit within the time window
        self.x_axis = list(np.linspace(0, self.display_time, self.num_points))
        self.notification_tolerance = self.notification_time * self.refresh_rate
        self.ave_cycle = list(range(1, self.naverage + 1))
        self.x_cycle = list(range(0, self.num_points))
        self.ave_idx = list(range(0, self.averaging_size + 1))  # +1 for NaN value added at the end
        self.bad_scan_limit = 3

        # motor variables
        self.manual_motor = True
        self.high_limit = 0.1
        self.low_limit = -0.1
        self.step_size = 0.02
        self.position_tolerance = 0.01
        self.motor_averaging = 10
        self.algorithm = 'Ternary Search'
        self.motor_mode = 'sleep'
        self.live_motor = True
        self.motor_position = 0
        self.read_motor_position = 0
        self.motor_connected = False
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

        self.image_calibration_steps = []
        self.image_calibration_positions = []
        self.contours = []
        self.best_fit_line = []
        self.best_fit_line_plus = []
        self.best_fit_line_minus = []
        self.com = []
        self.find_com_bool = False
        self.dilate = None
        self.erode = None
        self.open_operation = None
        self.close_operation = None
        self.brightness = None
        self.contrast = None
        self.blur = None
        self.threshold = 110

    def update_live_graphing(self, live):
        """
        Updates the live graphing mode.

        Parameters:
            live (bool): A boolean value indicating whether live graphing is enabled or not.

        """
        self.live_data = live
        self.signals.changeRunLive.emit(self.live_data)
        self.signals.updateRunValues.emit(self.live_data)

    def update_calibration_source(self, cal_src):
        """
        Updates the calibration source.

        Parameters:
            cal_src (str): The calibration source to be used.

        """
        self.calibration_source = cal_src
        self.signals.changeCalibrationSource.emit(self.calibration_source)

    def update_num_cali(self, nc):
        """
        Updates the number of calibration points.

        Parameters:
            nc (int): The number of calibration points.

        """
        self.num_cali = nc
        self.signals.changeNumberCalibration.emit(self.num_cali)

    def update_percent(self, p):
        """
        changes the percent threshold and emits a signal to the thread
        so that the range of allowed values and the graph will get updated

        Parameters:
            p (int): The percent threshold value.

        """
        self.percent = p
        if self.calibrated:
            self.signals.changePercent.emit(self.percent)

    def update_graph_averaging(self, avg):
        """
        updates the number of points to average on the graph.

        Parameters:
            avg (int): The number of points to average.

        """
        if avg < self.display_time:
            self.graph_ave_time = avg
        else:
            self.graph_ave_time = self.display_time

    def update_refresh_rate(self, rr):
        """
        updates the refresh rate of the graph.

        Parameters:
            rr (int): The refresh rate value.

        """
        self.refresh_rate = int(rr)
        self.signals.changeDisplayTime.emit(self.display_time, self.refresh_rate)

    def update_display_time(self, dis_t):
        """
        Updates the display time or the x-axis window.

        Parameters:
            dis_t (int): The display time value.

        """
        self.display_time = int(dis_t)
        self.signals.changeDisplayTime.emit(self.display_time, self.refresh_rate)

    def update_scan_limit(self, sl):
        """
        Updates the bad scan limit.

        Parameters:
            sl (int): The bad scan limit value.

        """
        self.bad_scan_limit = sl
        self.signals.changeScanLimit.emit(self.bad_scan_limit)

    def update_limits(self, high, low):
        """
        Updates the high and low limits for the motor.

        Parameters:
            high (float): The high limit value.
            low (float): The low limit value.

        """
        self.high_limit = high
        self.low_limit = low

    def update_step_size(self, ss):
        """
        Updates the step size for the motor.

        Parameters:
            ss (float): The step size value.

        """
        self.step_size = ss

    def update_motor_averaging(self, v):
        """
        Updates the number of points to average for each motor move.

        Parameters:
            v (int): The number of points to average.

        """
        self.motor_averaging = v

    def update_algorithm(self, a):
        """
        Updates the algorithm used for motor moving.

        Parameters:
            a (str): The algorithm name.

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
        """
        Retrieves the calibration results and file path.

        Returns:
            tuple: A tuple containing the calibration results (dict) and file path (str).

        """
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
        """
        Sets the mode of operation.

        Parameters:
            mode (str): The mode of operation.

        """
        self.mode = mode
        self.signals.changeStatusMode.emit(self.mode)

    def set_calibration_values(self, cal):
        """
        Sets the calibration values.

        Parameters:
            cal (dict): A dictionary containing calibration values.

        """
        self.calibration_values = cal
        self.calibrated = True

    def update_calibration_priority(self, p):
        """
        Updates the calibration priority.

        Parameters:
            p (str): The calibration priority string - either 'recalibrate' or 'keep calibration'

        """
        self.signals.changeCalibrationPriority.emit(p)

    def calibrate_image(self):
        """
        Initiate the image calibration process.
        """
        if self.motor_mode != "sleep":
            self.signals.message.emit("the motor is currently running an algorithm. Try stopping motor first")
        else:
            self.update_motor_mode('calibrate')

    def update_motor_mode(self, mode):
        """
        Update the motor mode.

        Args:
            mode (str): The new motor mode.
        """
        self.motor_mode = mode
        self.signals.motorMode.emit(self.motor_mode)

    def connect_motor(self):
        """
        Connect to the motor.
        """
        self.signals.connectMotor.emit()

    def update_live_motor(self, live):
        """
        Update the flag for live motor movement.

        Args:
            live (bool): Flag indicating whether live motor movement is enabled.
        """
        self.live_motor = live
        self.signals.liveMotor.emit(live)

    def update_motor_position(self, p):
        """
        Update the motor position.

        Args:
            p (float): The new motor position.
        """
        self.motor_position = p
        self.signals.changeMotorPosition.emit(self.motor_position)

    def update_read_motor_position(self, p):
        """
        Update the read motor position.

        Args:
            p (float): The new read motor position.
        """
        self.read_motor_position = p
        self.signals.changeReadPosition.emit(self.read_motor_position)

    def update_image_calibration_steps(self, cs):
        """
        Update the number of steps for image calibration.

        Args:
            cs (int): The new number of steps for image calibration.
        """
        self.image_calibration_steps = cs

    def update_peak_intensity(self, pi):
        """
        Update the peak intensity.

        Args:
            pi (float): The new peak intensity value.
        """
        self.peak_intensity = pi
        self.signals.changePeakIntensity.emit(self.peak_intensity)

    def update_jet_radius(self, r):
        """
        Update the jet radius.

        Args:
            r (float): The new jet radius.
        """
        self.radius = r
        self.signals.changeJetRadius.emit(self.radius)

    def update_jet_center(self, jc):
        """
        Update the jet center.

        Args:
            jc (tuple): The new jet center coordinates (x, y).
        """
        self.jet_center = jc
        self.signals.changeJetCenter.emit(self.jet_center)

    def update_max_intensity(self, mi):
        """
        Update the maximum intensity.

        Args:
            mi (float): The new maximum intensity value.
        """
        self.max = mi
        self.signals.changeMaxIntensity.emit(self.max)

    def update_background(self, bgn):
        """
        Update the background value.

        Args:
            bgn (float): The new background value.
        """
        self.bg = bgn
        self.signals.changeBackground.emit(self.bg)

    def update_dropped_shots(self, ds):
        """
        Update the percentage of dropped shots.

        Args:
            ds (float): The new percentage of dropped shots.
        """
        self.percent_dropped = ds
        self.signals.changeDroppedShots.emit(self.percent_dropped)

    def image_calibration_position(self, line_best_fit):
        """
        Add an image calibration position to the list.

        Args:
            line_best_fit (float): The line of best fit for the calibration position.
        """
        g = [self.read_motor_position, line_best_fit]
        self.image_calibration_positions.append(g)
        
    def run_image_search(self):
        """
        Run the image search algorithm.
        """
        self.update_algorithm("image search")
        self.signals.imageSearch.emit()

    def set_com_on(self, o):
        """
        Set the flag for COM detection.

        Args:
            o (bool): Flag indicating if COM detection is enabled.
        """
        self.find_com_bool = o
        self.signals.comDetection.emit()
