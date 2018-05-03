#!/bin/bash
# Starts the nvlmon monitor on the local host
# Measures gpu, gpu memory, bw, nvlink, powerw

NVLMON_PATH="http://9.47.154.11/mhchen/"
NVLMON_PREFIX="nvlmon_"
NVLMON_PLATFORM=$(uname -m)
NVLMON_FN=$NVLMON_PREFIX$NVLMON_PLATFORM

echo -e "nvlmon: Only IBM Power9/4GPU is fully support now. The next version will work for Power8/4GPU."
echo -e "nvlmon: This module is relied on nvlmon v1.7 and is supposed to used with ppc64le platform."

[ $# -ne 2 ] && echo USAGE: $0 TARGET_FN DELAY_SEC && exit 1
TARGET_FN=$1
DELAY_SEC=$2

# Check and download NVLMON binary
if [ ! -f $NVLMON_FN ]; then
    wget $NVLMON_PATH$NVLMON_FN
    chmod 755 $NVLMON_FN
fi

if [ ! -f $NVLMON_FN ]; then
    echo "ERROR: nvlmon not found at localhost and $NVLMON_PATH$NVLMON_FN" && exit 1
fi

# Check if a copy of this script is already running
NUM=`ps -efa | grep $0 | grep -v "vim\|grep\|ssh" | wc -l`
[ $NUM -gt 2 ] && echo WARNING: $0 appears to be running on $HOSTNAME

STOP_FN=/tmp/${USER}/viz_workload/stop-nvlmon
rm -f $STOP_FN

DIRNAME=`dirname $TARGET_FN`
mkdir -p $DIRNAME
rm -f $TARGET_FN

# Detect cpu and start monitoring
TCPU=$(cat /proc/cpuinfo |grep POWER9)
if [ ! -z "$TCPU" -a "$TCPU" != " " ]; then
    echo -e "IBM Power9 is detected ..."
    ./$NVLMON_FN -9 -e -t -p > $TARGET_FN
    ./$NVLMON_FN -9 -S $STOP_FN -d $DELAY_SEC -e -p >> $TARGET_FN &
    PID=$!
else
    TCPU=$(cat /proc/cpuinfo |grep POWER8)
    if [ ! -z "$TCPU" -a "$TCPU" != " " ]; then
        echo -e "IBM Power8 is detected ..."
        ./$NVLMON_FN -8 -e -t -p > $TARGET_FN
        ./$NVLMON_FN -8 -S $STOP_FN -d $DELAY_SEC -e -p >> $TARGET_FN &
        PID=$!
    else
        echo -e "Did not detect IBM Power 8/9, still try to monitor NVLink ..."
        ./$NVLMON_FN -e -t -p > $TARGET_FN
        ./$NVLMON_FN -S $STOP_FN -d $DELAY_SEC -e -p >> $TARGET_FN &
        PID=$!
    fi
fi

trap "kill $PID; exit 1" SIGTERM SIGINT # Kill PID on CTRL-C
# Kill on semaphore
while [ ! -e $STOP_FN ]; do
    sleep 1
done

kill $PID
rm -f $STOP_FN

