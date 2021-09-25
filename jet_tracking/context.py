import numpy as np
import logging
import threading

log = logging.getLogger(__name__)
lock = threading.Lock()


class Context(object):

    def __init__(self, signals):
        self.signals = signals
        self.JT_LOC = '/cds/group/pcds/epics-dev/espov/jet_tracking/jet_tracking/'
        self.SD_LOC = '/reg/d/psdm/'
        self.PV_DICT = {'diff': 'XCS:JTRK:REQ:DIFF_INTENSITY', 'i0': 'XCS:JTRK:REQ:I0', 'ratio': 'XCS:JTRK:REQ:RATIO'}
        self.CFG_FILE = 'jt_configs/xcs_config.yml'
        self.HUTCH = 'xcs'
        self.EXPERIMENT = 'xcsx1568'
        self.live_data = True
        self.calibration_source = "calibration from results"
        self.percent = 70
        self.graph_averaging = 50
        self.refresh_rate = 50
        self.display_time = 60
        self.buffer_size = 300
        self.notification_tolerance = 200
        self.dropped_shot_threshold = 1000
        self.manual_motor = True
        self.high_limit = 5
        self.low_limit = -5
        self.step_size = 10
        self.motor_averaging = 10
        self.algorithm = 'Ternary Search'
        self.calibration_values = {}
        self.isTracking = False
        self.calibrated = False
        self.live_data = True
        self.x_axis = list(np.linspace(0, self.display_time, self.buffer_size))
        # added while adding simulator
        self.motor_position = 0
        self.percent_dropped = 10
        self.peak_intensity = 1
        self.radius = 0.025
        self.center = 0.03
        self.max = 1.0
        self.bg = 0.05

        # added while adding simulator
    def update_motor_position(self, mp):
        self.motor_position = mp
        self.signals.changeMotorPosition.emit(self.motor_position)

    def update_dropped_shots(self, ds):
        self.percent_dropped = ds
        self.signals.changeDroppedShots.emit(self.percent_dropped)

    def update_peak_intensity(self, pi):
        self.peak_intensity = pi
        self.signals.changePeakIntensity.emit(self.peak_intensity)

    def update_jet_radius(self, r):
        self.radius = r
        self.signals.changeJetRadius.emit(self.radius)

    def update_jet_center(self, jc):
        self.center = jc
        self.signals.changeJetCenter.emit(self.center)

    def update_max_intensity(self, mi):
        self.max = mi
        self.signals.changeMaxIntensity.emit(self.max)

    def update_background(self, bgn):
        self.bg = bgn
        self.signals.changeBackground.emit(self.bg)
    #

    def update_live_graphing(self, live):
        self.live_data = live
        self.signals.changeRunLive.emit(self.live_data)

    def update_calibration_source(self, cal_src):
        self.calibration_source = cal_src
        self.signals.changeCalibrationSource.emit(self.calibration_source)

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
        self.graph_averaging = avg
        self.signals.changeGraphAve.emit(self.graph_averaging)

    def update_refresh_rate(self, rr):
        """
        changes the refresh rate of the graph
        """
        self.refresh_rate = rr
        self.signals.changeRefreshRate.emit(self.refresh_rate)

    def update_display_time(self, dis_t):
        self.display_time = dis_t
        self.x_axis = list(np.linspace(0, self.display_time, self.buffer_size))
        self.signals.changeDisplayTime.emit(self.display_time)

    def update_manual_motor(self, manual):
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
        self.signals.changeAlgorithm.emit(self.algorithm)

    def parse_config(self):
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

    def get_cal_results(self, hutch, exp):
        results_dir = Path(f'/cds/home/opr/{hutch}opr/experiments/{exp}/jt_calib/')
        cal_files = list(results_dir.glob('jt_cal*'))
        cal_files.sort(key=os.path.getmtime)
        if cal_files:
            cal_file_path = cal_files[-1]
            with open(cal_file_path) as f:
                cal_results = json.load(f)
            return cal_results, cal_file_path
        else:
            return None

    def set_mode(self, mode):
        self.mode = mode
        self.signals.mode.emit(self.mode)

    def update_tracking(self, tracking):
        self.isTracking = tracking
        self.signals.enableTracking.emit(self.isTracking)

    def set_calibrated(self, c):
        self.calibrated = c

    def set_calibration_values(self, cal):
        self.calibration_values = cal
