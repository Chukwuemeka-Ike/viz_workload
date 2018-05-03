#!/bin/bash

# Fix buggy perl LC_*
export LC_CTYPE=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Export CUDA library paths
export PATH=/usr/local/cuda/bin:/usr/local/cuda/include:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
export LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/powerpc64le-linux-gnu/:/usr/local/cuda/targets/ppc64le-linux/lib/:/usr/local/cuda/lib64:/usr/local/cuda/lib64/stubs:/usr/local/cuda/extras/CUPTI/lib64/

# Required variables
export WORKLOAD_NAME=EXAMPLES             # A short name for this type of workload
export DESCRIPTION="NVLMON host-to-device bandwidthTest example"  # A description of this particular workload

# Find the 'bandwidthTest' binary installed on local system
FILES=`find /usr/local/cuda/ -name bandwidthTest`
for FN in $FILES; do
    COUNT=`ls -l $FN | perl -pe "s/[rwx-]+([rwx-]) .*/\1/" | wc -l`
    # directories return COUNT > 1
    if [ $COUNT -eq 1 ]; then
        # check if file is executable
        [ `ls -l $FN | perl -pe "s/[rwx-]+([rwx-]) .*/\1/"` == 'x' ] && \
            FOUND=1 && break
    fi
done

if [ -z $FOUND ]; then
    echo "bandwidthTest binary not found.  You may need to compile this at:"
    echo "$ cd /usr/local/cuda/samples/1_Utilities/bandwidthTest"
    echo "$ sudo make"
    exit 1
fi

export WORKLOAD_CMD="$FN --mode=shmoo"

# Optional variables (defaults shown here)
export WORKLOAD_DIR="."             # The workload working directory
export MEAS_DELAY_SEC=1             # Delay in seconds between each measurement
export VERBOSE=0                    # Verbosity level 0|1|2  Higher==more messages
# What measurements to collect (space delimited). See 'available-measurements.txt'
export MEASUREMENTS="sys-summary nvlmon"         # cpu, memory, io and network vs time, and nvlmon

export RUNDIR=`./create-rundir.sh`

for ITER in `seq 4`; do
  export RUN_ID="ITER${ITER}"
  ./run-and-measure.sh
done
