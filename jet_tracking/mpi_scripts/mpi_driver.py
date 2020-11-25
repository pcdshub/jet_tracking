# Local imports
from mpi_worker import MpiWorker
from mpi_master import MpiMaster
from utils import get_r_masks, get_evr_w_codes
from mpi4py import MPI
import psana
import yaml
import re
import argparse

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

# All the args
parser = argparse.ArgumentParser()
parser.add_argument('--exprun', help='psana experiment/run string (e.g. exp=xppd7114:run=43)', type=str, default='')
#parser.add_argument('--dsname', help='data source name', type=str, default='')
parser.add_argument('--nevts', help='number of events', default=50, type=int)
parser.add_argument('--cfg_file', help='if specified, has information about what metadata to use', type=str, default='default_config.yml')
args = parser.parse_args()

# Two options for now, offline data or shared memory
if args.exprun:
    info = re.split('=|:', args.exprun)
    exp = info[1]
    hutch = exp[:3]
    exp_dir = ''.join(['/reg/d/psdm/', hutch, '/', exp, '/xtc/'])
    dsname = ''.join([args.exprun, ':smd:', 'dir=', exp_dir]) 
else:
    dsname = 'shmem=psana.0:stop=no'
    psana.setOption('psana.calib-dir', '/reg/d/psdm/cxi/cxilv9518/calib/')

# Parse config file to hand to workers
with open(''.join(['mpi_configs/', args.cfg_file])) as f:
    yml_dict = yaml.load(f, Loader=yaml.FullLoader)
    api_port = yml_dict['api_msg']['port']
    det_map = yml_dict['det_map']
    ipm_name = yml_dict['ipm']['name']
    ipm_det = yml_dict['ipm']['det']
    pv_map = yml_dict['pv_map']
print('here is pv map!!! ', pv_map)
# No way to do this only once with MPI
ds = psana.DataSource(dsname)
# Main detector we're looking at
detector = psana.Detector(det_map['name'])
# Intensity monitor, could be wave8 or gdet with detector
ipm = (psana.Detector(ipm_name), ipm_det)
# Because we never know hich evr will have event codes
evr = get_evr_w_codes(psana.DetNames())
# Get the R masks, would be great to do this only once
r_mask = get_r_masks(det_map['shape'])
print(psana.DetNames())
if rank == 0:
    master = MpiMaster(rank, api_port, det_map, pv_map)
    master.start_run()
else:
    worker = MpiWorker(ds, args.nevts, detector, ipm, evr, r_mask)
    worker.start_run()
