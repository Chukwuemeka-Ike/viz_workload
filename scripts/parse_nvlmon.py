#!/usr/bin/python
'''
Input:  filename containing raw csv measured using nvlmon utility
Output: multiple timeseries files
        1) individual gpu utilization, mem utilization, and power usage CSV and JSON
        2) average GPU and memory utilization (CSV)
'''

import sys
import json
import re
from datetime import datetime
from common import csv_to_json

def validate(csv_str):
    '''
    Verify a consistent number of columns in the csv string
    Strip last record if incomplete
    '''
    lines = csv_str.split('\n')
    len0 = len(lines[0].split(','))
    len1 = len(lines[-1].split(','))
    while len0 != len1:
        lines.pop()
        len1 = len(lines[-1].split(','))
    return '\n'.join(lines)

def mean(numbers):
    ''' Calculate mean of array of numbers '''
    return float(sum(numbers)) / max(len(numbers), 1)

def calc_avg(gpu_str, mem_str, membw_str):
    '''
    Input (example for 4 GPUs):
        gpu_str = "t1,0,0,100,0\nt2,0,0,40,0\n"
        mem_str = "t1,0,0,8,0\nt2,0,0,20,0\n"
    Output (tstamp, gpu_avg, mem_avg):
        avg_str = "t1,25,2\nt2,10,5"
    '''
    avg_str = ''
    gpu_lines = gpu_str.split('\n')
    mem_lines = mem_str.split('\n')
    membw_lines = membw_str.split('\n')
    while gpu_lines:
        line = gpu_lines.pop(0)
        fields = line.split(',')
        avg_str += '%s,%.1f,' % (fields[0], mean([float(i) for i in fields[1:]]))
        line = mem_lines.pop(0)
        fields = line.split(',')
        avg_str += '%.1f,' % (mean([float(i) for i in fields[1:]]))
        line = membw_lines.pop(0)
        fields = line.split(',')
        avg_str += '%.1f\n' % (mean([float(i) for i in fields[1:]]))
    return avg_str


def parse_raw_gpu(raw_fn):
    '''
    Read gpu data from nvlmon utility and return individual CSV strings
    Format: timestamp,NumGPUs,
    GPU0_name,GPU0_CoreUtil,GPU0_MemBWUtil,GPU0_TotalMem,GPU0_UsedMem,GPU0_Power,GPU0_Temp,GPU0_PCIeRX,GPU0_PCIeTX,GPU0_NVLinks,[GPU0_nvlink0_rxrate,GPU0_nvlink0_txrate](* GPU0_NVLinks)
    '''
    with open(raw_fn, 'r') as fid:
        lines = fid.readlines()
    line = lines.pop(0)  # discard header
    time0 = False
    topology = 0
    num_gpu = 0
    num_nvlink = 0
    gpu_str = '0'
    membw_str = '0'
    mem_str = '0'
    pow_str = '0'
    temp_str = '0'
    pcie_str = [None] * 128
    nvl_str = [None] * 128
    int_str = [None] * 128
    for i in range(128): # assume no larger than 128 gpu pre cluster 
        pcie_str[i] = "" 
        nvl_str[i] = ""
        int_str[i] = '0'
    len0 = 0

    while lines:
        line = lines.pop(0)
        try:
            item = line.split(',')
            time = item[0]
            etime = 1

            if not time0:
                len0 = len(item)
                time0 = time
                num_gpu = int(item[1])
                num_nvlink = item[11]
                if int(num_nvlink) == 6:  # power9, so far no power/6gpu topology data, so do not do that
                    if int(num_gpu) == 4: # power9/4gpu, supported, 0,4,8 p2p recv; 1,5,9 p2p send; 2,6,10 h2d; 3,7,11 d2h
                        print ("Topology: Power9/4 GPUs")
                        topology = 964
                elif int(num_nvlink) == 4:  # power8
                    if int(num_gpu) == 4: # power8/4gpu, supported
                        print ("Topology: Power8/4 GPUs")
                        topology = 844
                else:  # something have nvlink but does not power8/9?
                    topology = int(num_nvlink)
            else:
                if len0 <> len(item):
                    break # skip incomplete data
                etime = long(time) - long(time0)
                gpu_str += '\n' + str(etime)
                membw_str += '\n' + str(etime)
                mem_str += '\n'+ str(etime)
                pow_str += '\n' + str(etime)
                temp_str += '\n' + str(etime)
                for i in range(num_gpu):
                    pcie_str[i] = ""
                    nvl_str[i] = ""
                    int_str[i] += '\n' + str(etime)
                    #pcie_str[i] += '\n' + str(etime)
                    #nvl_str[i] += '\n' + str(etime)
            # init 2, (10 + num of nvlinks fields) pre gpu (22 for p9)
            curidx = 2
            for i in range(num_gpu):
                #item[i] is name
                gpu_str += ',' + item[curidx+1]
                membw_str += ',' + item[curidx+2]
                if long(item[curidx + 4]) == long(item[curidx + 3]):
                    mem_str += ",0" # 0%
                else:
                    mem_str += ',' + str((float(item[curidx+4]) / float(item[curidx+3])) * 100)  # convert to % usage
                if long(item[curidx + 5]) > 0:
                    pow_str += ',' + str(float(item[curidx + 5]) / 1000)  # unit: w
                else:
                    pow_str += ',' + item[curidx + 5]  # 0
                temp_str += ',' + item[curidx+6]
                pcie_str[i] += ',' + item[curidx+7] + ',' + item[curidx+8]
                # item[curidx + 9] / item[11] is the number of nvlinks
                NVLIDX = curidx+10
                if topology == 964:  # power9/4gpu, supported, 0,4,8 p2p recv; 1,5,9 p2p send; 2,6,10 h2d; 3,7,11 d2h
                    p2p_recv=long(item[NVLIDX]) + long(item[NVLIDX + 4]) + long(item[NVLIDX+8])
                    p2p_send=long(item[NVLIDX+1]) + long(item[NVLIDX + 5]) + long(item[NVLIDX+9])
                    h2d=long(item[NVLIDX+2]) + long(item[NVLIDX + 6]) + long(item[NVLIDX+10])
                    d2h=long(item[NVLIDX+3]) + long(item[NVLIDX + 7]) + long(item[NVLIDX+11])
                    nvl_str[i] += "," + str(float(p2p_recv) / 1024 / 1024 / etime)
                    nvl_str[i] += "," + str(float(p2p_send) / 1024 / 1024 / etime)
                    nvl_str[i] += "," + str(float(h2d) / 1024 / 1024 / etime)
                    nvl_str[i] += "," + str(float(d2h) / 1024 / 1024 / etime)
                    curidx = NVLIDX + 12
                elif topology == 844:  # power8/4gpu, supported, 0,2 p2p recv; 1,3 p2p send; 4,6 h2d; 5,7 d2h, this mapping is incorrect, FIXIT
                    p2p_recv=long(item[NVLIDX]) + long(item[NVLIDX + 2])
                    p2p_send=long(item[NVLIDX+1]) + long(item[NVLIDX + 3])
                    h2d=long(item[NVLIDX+4]) + long(item[NVLIDX + 6])
                    d2h=long(item[NVLIDX+5]) + long(item[NVLIDX + 7])
                    nvl_str[i] += "," + str(float(p2p_recv) / 1024 / 1024 / etime)
                    nvl_str[i] += "," + str(float(p2p_send) / 1024 / 1024 / etime)
                    nvl_str[i] += "," + str(float(h2d) / 1024 / 1024 / etime)
                    nvl_str[i] += "," + str(float(d2h) / 1024 / 1024/ etime)
                    curidx = NVLIDX + 8
                else: # something have nvlink but does not power8/9?, did not test yet.
                    for r in range(int(item[curidx+8])):  # get nvlinks, should be equal to num_nvlink
                        nvl_str[i] += "," + float(item[NVLIDX + r])/1024/1024/etime
                    print ("Warning: Unknown topology")
                    curidx = NVLIDX + int(item[curidx + 9]) + 1
                int_str[i] = int_str[i] + pcie_str[i] + nvl_str[i]
        except Exception as err:
            print(str(err))
            print(err.args)
            print(line)
            pass
    return (num_gpu, topology, gpu_str, membw_str, mem_str, pow_str, temp_str, pcie_str, nvl_str, int_str)

def main(raw_fn):
    '''
    Parse each line of input file and construct CSV strings, then convert to JSON
    '''
    num_gpu, topology, gpu_str, membw_str, mem_str, pow_str, temp_str, pcie_str, nvl_str, int_str = parse_raw_gpu(raw_fn)
    # Often the last set of data is incomplete. Clean the csv records
    ext = ['.gpu', '.mem', '.pow','.membw', '.temp']
    header = 'time_sec,' + ','.join(['gpu' + str(i) for i in range(num_gpu)])
    header += '\n'
    # Save data for all individual gpu traces
    for csv_str in [gpu_str, membw_str, mem_str, pow_str, temp_str]:
        csv_str = header + csv_str
        ext_str = ext.pop(0)
        out_fn = raw_fn.replace('data/raw', 'data/final') + ext_str + '.csv'
        with open(out_fn, 'w') as fid:
            fid.write(csv_str)
        obj = csv_to_json(csv_str)
        out_fn = raw_fn.replace('data/raw', 'data/final') + ext_str + '.json'
        with open(out_fn, 'w') as fid:
            fid.write(json.dumps(obj))
    # Now calculate average GPU & Memory usage for all traces and save
    header = 'time_sec,GPU,MEMORY,MEM_BW\n'
    avg_str = calc_avg(gpu_str, mem_str, membw_str)
    out_fn = raw_fn.replace('data/raw', 'data/final') + '.avg.csv'
    with open(out_fn, 'w') as fid:
        fid.write(header + avg_str)

    header = 'time_sec'
    header += ",PCIeRx,PCIeTx,NVDevRx,NVDevTx,NVH2D,NVD2H\n"
    for i in range(num_gpu):
        out_fn = raw_fn.replace('data/raw', 'data/final') + '.nvl%d.csv' % (i)
        with open(out_fn, 'w') as fid:
            fid.write(header + int_str[i])



if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write("USAGE: {} <raw_fn>\n".format(sys.argv[0]))
        sys.exit(1)
    main(sys.argv[1])
