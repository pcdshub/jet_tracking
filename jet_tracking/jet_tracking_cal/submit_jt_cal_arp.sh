#!/bin/bash

usage()
{
cat << EOF
$(basename "$0"): 
	Script to launch a smalldata_tools run analysis
	
	OPTIONS:
		-h|--help
			Definition of options
		-q|--queue
			Queue to use on SLURM
        -t|--tasks
            Number of parallel tasks
        -s|--script
            Script to run with full path
        -c|--config
            Configuration file you want to use for jt cal
        -r|--run
            Run to use for calibration
EOF

}

source /reg/g/psdm/etc/psconda.sh -py3

# Use getopts when we get a chance
POSITIONAL=()
while [[ $# -gt 0 ]]
do
        key="$1"

	case $key in
		-h|--help)
			usage
			exit
			;;
		-q|--queue)
			QUEUE="$2"
			shift
			shift
			;;
        -t|--tasks)
   		    TASKS="$2"
			shift
			shift
			;;
        -s|--script)
            SCRIPT="$2"
            shift
            shift
            ;;
        -c|--config)
            CONFIG="$2"
            shift
            shift
            ;;
        -r|--run)
            RUN="$2"
            shift
            shift
            ;;
        *)
            POSITIONAL+=("$1")
			shift
			;;                     
	esac
done
set -- "${POSITIONAL[@]}"

# Need to setup for FFB
QUEUE=${QUEUE:='psanaq'}
#QUEUE=${QUEUE:='psfehhiprioq'}
TASKS=${TASKS:=10}
SCRIPT=${SCRIPT:=/cds/group/pcds/epics-dev/espov/jet_tracking/jet_tracking/jet_tracking_cal/jt_cal.py}
CONFIG=${CONFIG:=/cds/group/pcds/epics-dev/espov/jet_tracking/jet_tracking/jt_configs/xcs_config.yml}

sbatch -p $QUEUE --ntasks-per-node 10 --ntasks $TASKS --job-name="jet track cal" --wrap="mpirun python -u $SCRIPT --cfg $CONFIG --run $RUN"
