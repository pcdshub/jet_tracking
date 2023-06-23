import argparse
import json
import logging
import os
import sys
from pathlib import Path

import psana
import yaml
from mpi4py import MPI

from .mpi_master import MpiMaster
from .mpi_worker import MpiWorker

fpath = os.path.dirname(os.path.abspath(__file__))
fpathup = '/'.join(fpath.split('/')[:-1])
sys.path.append(fpathup)

from utils import get_r_masks  # noqa: E402

logger = logging.getLogger(__name__)

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

# All the args
parser = argparse.ArgumentParser()
parser.add_argument('--cfg_file', help='if specified, has information about '
                    'what metadata to use', type=str, default='xcs_config.yml')
args = parser.parse_args()

# Parse config file to hand to workers
with open(args.cfg_file) as f:
    yml_dict = yaml.load(f, Loader=yaml.FullLoader)
    api_port = yml_dict['api_msg']['port']
    det_map = yml_dict['det_map']
    ipm_name = yml_dict['ipm']['name']
    ipm_det = yml_dict['ipm']['det']
    pv_map = yml_dict['pv_map']
    jet_cam_name = yml_dict['jet_cam']['name']
    jet_cam_axis = yml_dict['jet_cam']['axis']
    sim = yml_dict['sim']
    hutch = yml_dict['hutch']
    exp = yml_dict['experiment']
    run = yml_dict['run']
    evr_name = yml_dict['evr_name']
    event_code = yml_dict['event_code']
    # wf_length = yml_dict['wf_length']

if jet_cam_name == 'None' or jet_cam_name == 'none':
    jet_cam_name = None

# Get calibration results
calib_dir = Path(''.join(['/cds/data/psdm/', hutch, '/', exp, '/calib/']))
jt_dir = Path(''.join([str(calib_dir), '/jt_results/']))

# cal_files = sorted(os.listdir(jt_dir))
cal_files = list(jt_dir.glob('jt_cal*'))
cal_files.sort(key=os.path.getmtime)
if cal_files:
    cal_file_path = cal_files[-1]
    # cal_file_path = ''.join([jt_dir, cal_file])
    print(f'Calibration file: {cal_file_path}')
    with open(cal_file_path) as f:
        cal_results = json.load(f)
else:
    logger.warning('You must run a calibration before starting jet tracking')
    sys.exit()

if sim:
    # Run from offline data
    exp_dir = ''.join(['/cds/data/psdm/', hutch, '/', exp, '/xtc/'])
    dsname = ''.join(['exp=', exp, ':run=', run, ':smd:', 'dir=', exp_dir])
else:
    # Run on shared memeory
    dsname = 'shmem=psana.0:stop=no'
    psana.setOption('psana.calib-dir', calib_dir)

ds = psana.DataSource(dsname)
detector = psana.Detector(det_map['name'])
ipm = (psana.Detector(ipm_name), ipm_det)
if jet_cam_name is not None:
    jet_cam = psana.Detector(jet_cam_name)
else:
    jet_cam = None
evr = psana.Detector(evr_name)
r_mask = get_r_masks(det_map['shape'])

if rank == 0:
    master = MpiMaster(rank, api_port, det_map, pv_map, sim=sim)
    master.start_run()
else:
    peak_bin = int(cal_results['peak_bin'])
    delta_bin = int(cal_results['delta_bin'])
    worker = MpiWorker(ds, detector, ipm, jet_cam, jet_cam_axis, evr, r_mask,
                       cal_results, event_code=event_code)
    print('Worker')
    worker.start_run()
