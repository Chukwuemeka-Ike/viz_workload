# This script demonstrates how to sweep a parameter
# and access/view all resulting data from the same web page

# Required variables are WORKLOAD_NAME, DESCRIPTION, & WORKLOAD_CMD
#export WORKLOAD_NAME=cchen01_default_platform_worker        # A short name for this type of workload
export WORKLOAD_NAME=cchen01_default_platform_worker1_MB        # A short name for this type of workload

#export HOSTS="cs-fw-r4-fw1 cs-host-r4-sm1"
export HOSTS="cs-host-r4-sm1 cs-fw-r4-fw1 cs-fw-r2-fw1"
export CONTINUE_ON_ERROR=1


# Optional variables (defaults shown here)
export WORKLOAD_DIR="/home/cchen01/src-pytorch-distributed/Pytorch/examples/imagenet"             # The workload working directory
export MEAS_DELAY_SEC=2             # Delay in seconds between each measurement
export VERBOSE=0                    # Verbosity level 0|1|2  Higher==more messages
# What measurements to collect (space delimited). See 'available-measurements.txt'
#export MEASUREMENTS="sys-summary cpu-heatmap interrupts gpu"   # cpu, memory, io and network vs time
export MEASUREMENTS="sys-summary gpu pcie"   # cpu, memory, io and network vs time

# For sweeps, create a run directory where all files will be saved
# Specify it directly, like this:
#export RUNDIR=path/to/your/directory
# or use this script to create one automatically (recommended)
export RUNDIR=`./create-rundir.sh`


#for GPU in 8 4 2 1 6 3 7 5; do
#for GPU in 4 1; do
#i="1"
#gid="0"
#while [ $i -lt $GPU ]
#do
#gid=$gid","$i
#i=$[$i+1]
#done

export CUDA_VISIBLE_DEVICES=1
#echo $CUDA_VISIBLE_DEVICES
  #export WORKLOAD_CMD="./load-cpu.sh $CPU"   # The workload to run
  #export WORKLOAD_CMD="cd /home/cchen01/rudra_dnn/cpp; mpirun --n 3 ./rudra_wildfire -groupSize 2 -f ../examples/imagenet/cfg_res.json -allowedGPU \"0,0,1\" ;cd -"   # The workload to run
#for WK in 1 2 4; do
  export WORKLOAD_CMD="cd /home/cchen01/src-pytorch-distributed/Pytorch/examples/imagenet;  ./default_platform_worker1_MB64;  cd -"   # The workload to run
  export RUN_ID="default_platform_worker1_MB64"               # Unique for this run
  export DESCRIPTION="cs-host-r4-sm1 default_platform_worker1_MB"  # A description of this particular workload
echo $CUDA_VISIBLE_DEVICES
echo $WORKLOAD_CMD
#ssh cs-fw-r1-fw2.pok.ibm.com /home/ihchung/start_pcie.sh &
  ./run-and-measure.sh
#ssh cs-fw-r1-fw2.pok.ibm.com /home/ihchung/stop_pcie.sh
#done
