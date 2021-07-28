
import logging
import threading

log = logging.getLogger(__name__)
lock = threading.Lock()

class Context():
    def __init__(self, signals):
        self.signals = signals
        self.JT_LOC = '/cds/group/pcds/epics-dev/espov/jet_tracking/jet_tracking/'
        self.SD_LOC = '/reg/d/psdm/'
        self.PV_DICT = {'diff': 'XCS:JTRK:REQ:DIFF_INTENSITY', 'i0': 'XCS:JTRK:REQ:I0', 'ratio': 'XCS:JTRK:REQ:RATIO'}
        self.CFG_FILE = 'jt_configs/xcs_config.yml'
        self.HUTCH = 'xcs'
        self.EXPERIMENT = 'xcsx1568'
        self.initialize_control_options()

    def initialize_control_options(self):
        self.thread_options = {}
        self.motor_options = {}
        self.calibration_values = {}
        self.live_data = True
        self.isTracking = False
        self.calibrated = False
        print(self.calibrated)

    def update_thread_options(self, thr, name, val):
        if thr == 'status':
            self.thread_options[name] = val
            self.send_status_update()
        elif thr == 'motor':
            self.motor_options[name] = val
            self.send_motor_update()

    def run_live(self, live):
        self.live_data = live
        self.signals.run_live.emit(self.live_data)

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

    def set_tracking(self, tracking):
        self.isTracking = tracking
        self.signals.enable_tracking.emit(self.isTracking)

    def set_calibrated(self, c):
        self.calibrated = c

    def send_status_update(self):
        self.signals.threadOp.emit(self.thread_options)

    def send_motor_update(self):
        self.signals.motorOp.emit(self.motor_options)

    def set_calibration_values(self, cal):
        self.calibration_values = cal
