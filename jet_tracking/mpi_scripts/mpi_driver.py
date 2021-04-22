from mpi_worker import MpiWorker
from mpi_master import MpiMaster
from utils import get_r_masks, get_evr_w_codes
from mpi4py import MPI
import psana
import yaml
import re
import json
import argparse
import os
import sys
import logging

logger = logging.getLogger(__name__)

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

# All the args
parser = argparse.ArgumentParser()
parser.add_argument('--cfg_file', help='if specified, has information about what metadata to use', type=str, default='xcs_config.yml')
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

# Get calibration results
calib_dir = ''.join(['/cds/data/psdm/', hutch, '/', exp, '/calib/'])
jt_dir = ''.join([calib_dir, 'jt_results/'])

cal_files = sorted(os.listdir(jt_dir))
if cal_files:
    cal_file = cal_files[-1]
    cal_file_path = ''.join([jt_dir, cal_file])
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
jet_cam = psana.Detector(jet_cam_name)
evr = get_evr_w_codes(psana.DetNames())
r_mask = get_r_masks(det_map['shape'])

if rank == 0:
    master = MpiMaster(rank, api_port, det_map, pv_map, sim=sim)
    master.start_run()
else:
    peak_bin = int(cal_results['peak_bin'])
    delta_bin = int(cal_results['delta_bin'])
    worker = MpiWorker(ds, detector, ipm, jet_cam, jet_cam_axis, evr, r_mask, peak_bin=peak_bin, delta_bin=delta_bin)
    worker.start_run()
