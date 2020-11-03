# EXPRUN = 'exp=cxilv9518:run=148'
# INFO = re.split('=|:', EXPRUN)
# EXP = INFO[1]
# HUTCH = EXP[:3]
# # Number of bins
# BINS = 100
# # Number of events to process
# EVENTS = 1000
# EXPDIR = ''.join(['/reg/d/psdm/', HUTCH, '/', EXP, '/xtc/'])
# DSNAME = ''.join([EXPRUN, ':smd:', 'dir=', EXPDIR])
import os
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('--exp', type=str, default=(os.environ['EXPERIMENT']))
parser.add_argument('--run', type=str, default=(os.environ['RUN_NUM']))
parser.add_argument('--cfg', type=str, default=(''))