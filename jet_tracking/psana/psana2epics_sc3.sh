#!/bin/bash

unset PYTHONPATH
unset LD_LIBRARY_PATH

export set EPICS_SITE_CONFIG=/reg/g/pcds/package/epics/3.14/RELEASE_SITE
source /reg/g/pcds/setup/epicsenv-cur.sh
export EPICS_CA_MAX_ARRAY_BYTES=12000000

source /reg/g/psdm/etc/psconda.sh > /dev/null

SOURCE="${BASH_SOURCE[0]}"
# resolve $SOURCE until the file is no longer a symlink
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
  # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done

DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

cd $DIR

args="$@"
python psana2epics_sc3.py $args
