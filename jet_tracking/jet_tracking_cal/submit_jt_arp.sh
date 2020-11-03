#!/bin/bash
# Script to get the data for a jet tracking calibration
source /reg/g/psdm/etc/psconda.sh
ABS_PATH=/cds/home/a/aegger/jet_tracking/jet_tracking/jet_tracking_cal
sbatch --nodes=2 --time=5 $ABS_PATH/jt_cal.py "$@"