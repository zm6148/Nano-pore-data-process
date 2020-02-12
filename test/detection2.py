import csv
import h5py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy import stats
import scipy as sp
from operator import itemgetter
from itertools import groupby
from sklearn.feature_selection import VarianceThreshold
from sklearn import cluster
from sklearn import metrics
from sklearn.datasets.samples_generator import make_blobs
from sklearn.preprocessing import StandardScaler
import heapq
import os
from scipy.signal import argrelextrema
from tkinter import filedialog
import tkinter as tk
import pandas as pd
from fast5_research.fast5_bulk import BulkFast5
from scipy.signal import hilbert, chirp
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

def empty(seq):
    try:
        return all(map(empty, seq))
    except TypeError:
        return False

file_path = os.path.dirname(os.path.realpath(__file__))
root = tk.Tk()
root.withdraw()
file_name = filedialog.askopenfilename(parent=root, initialdir=file_path + "\\fast5_data", title='Please select the fast5 file to process')
print (file_name + " selected.")

## ask for which channel to select
#select channels
case = 0
while case != 1 and case != 2:
    try:
        case = int(input("Indiviaul channel (1) or range of channels (2): "))
    except ValueError or case > 2:
        print ("please choose type 1 or 2")
             
if case == 1:
    number = input("Which Channel(s) to process: ")
    channels = list(map(int, number.split()))
elif case == 2: 
    start_channel = int(input("Start Channel number: "))
    end_channel = int(input("end Channel number: "))
    channels = list(range(start_channel, end_channel+1))

## ask for screening threshold for width and depth and width
width = input("Input the range for width in [s]: ")
width = list(map(float, width.split()))
print ("Range for width selection is set to from " + str(width[0]) + ' to ' + str(width[1]) ) 

depth = input("Input the range for depth in [mV]: ")
depth = list(map(float, depth.split()))
print ("Range for depth selection is set to from " + str(depth[0]) + ' to ' + str(depth[1]) ) 

bins_width = input("Histogram bin number for width: ")
print ("Histogram bin number for width is set to: " + bins_width) 

bins_depth = input("Histogram bin number for depth: ")
print ("Histogram bin number for depth is set to: " + bins_depth) 

## load selected file
f=h5py.File(file_name,'r')
# all keys
all_keys = list(f.keys())
#channel = 500;

all_channel_total_time = 0
all_channel_total_event = 0
all_channel_event_detail = []

name = file_name.split("/")[-1]

# write down each channel detail
with open(file_path + '\\processed_data\\' + name + '_channel_data_analysis.csv', 'a') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', 
                            quoting=csv.QUOTE_MINIMAL,
                            lineterminator='\r')
                                
    spamwriter.writerow(['Channel', 
                         'Events', 
                         'Time', 
                         'Capture rate']);   

for channel in channels:
    
    channel_name = 'Channel_' + str(channel)
    
    print('Processing ' + file_name + '_' + channel_name)
    ################################################################################
    # read data from fast5 data file
    # IntermediateData all_keys[0]
    # data_start_index=np.asarray(f[all_keys[0]][channel_name]['Reads']['read_start'])
    # data_length = np.asarray(f[all_keys[0]][channel_name]['Reads']['read_length'])
    # data_type = f[all_keys[0]][channel_name]['Reads']['classification']
    
    data_start_end_index = np.asarray(f[all_keys[0]][channel_name]['Events']['start'])
    data_start_end_mean = np.asarray(f[all_keys[0]][channel_name]['Events']['mean'])
    data_length_index = np.asarray(f[all_keys[0]][channel_name]['Events']['length'])
    data_start_end_flag = np.asarray(f[all_keys[0]][channel_name]['Events']['flags'])
    
    event_index_start = []
    event_index_end = []
    for ii in range(0,len(data_start_end_index)):
        if  ((data_start_end_flag[ii] == 33 or data_start_end_flag[ii] == 99) and data_start_end_mean[ii] > 0):
            event_index_start.append(data_start_end_index[ii])
    for ii in range(1,len(data_start_end_index)):
        if  data_start_end_flag[ii] == 17 or data_start_end_flag[ii] == 83:
            event_index_end.append(data_start_end_index[ii])
    
    event_index_pair = []
    ii = 0
    jj = 0
    while ii < len(event_index_start) and jj < len(event_index_end):
        index_start = event_index_start[ii]
        index_end = event_index_end[jj]
        if index_start < index_end:
            event_index_pair.append([index_start, index_end])
            ii = ii + 1
        else:
            jj = jj + 1
    
    if len(event_index_pair) == 0:
        print('no event in this channel, continue')
        continue
             
    # if len(event_index_end) >= len(event_index_start):
    #     length = len(event_index_start)
    # else:
    #     length = len(event_index_end)
        
    # for ii in range(0, len(event_index_start)):
    #     index_start = event_index_start[ii]
    #     for jj in range(0,len(event_index_end)):
    #         index_end = event_index_end[jj]
    #         if index_start < index_end:
    #             event_index_end.pop(jj)
    #             continue
    #     event_index_pair.append([index_start, index_end])
                
        
    # event 69 start
    # find event index
    # index_of_start = np.where(data_type == 69)
    # index_of_end = np.where(data_type == 80)
    # data_event_start_index = data_start_index[index_of_start]
    # data_event_end_index = data_start_index[index_of_end]
    # data_event_length = data_length[index_of_start]
    # event_index_pair = []
    # for ii in range(0, len(data_event_start_index)):
    #     event_index_pair.append([data_event_start_index[ii], data_event_start_index[ii] +  data_event_length[ii]])
    
    # raw data
    f = BulkFast5(file_name)
    r = pd.DataFrame()
    data = pd.DataFrame(f.get_raw(channel))
    data['channel'] = channel
    data['sample'] = range(len(data))
    data.columns = ['current', 'channel', 'sample']
    r = r.append(data)
    #get time
    sr = f.sample_rate
    r['time'] =  r['sample']/sr # add time column
    r_current_np = a = np.asarray(r['current'])
    Fs = sr
    
    ################################################################################
    # segment data
    theta=np.median(np.absolute(r_current_np)/0.6745)
    thr_low = -theta
    thr_high = theta
    
    negative_index_all = []
    negative_index_pair = []
        
    for ii in range(0, len(r_current_np)):
        if (r_current_np[ii] < -40) :
            negative_index_all.append(ii)
    run = []
    result = [run]
    expect = None
    for v in negative_index_all:
        if (v == expect) or (expect is None):
            run.append(v)
        else:
            run = [v]
            result.append(run)
        expect = v + 1
            
    for ele in result:
        negative_index_pair.append([ele[0], ele[-1]])
    
    
    ## based on negative current segment to data into partitions
    segment_pair = [[0,negative_index_pair[0][0]]]
    for ii in range(1, len(negative_index_pair)):
        segment_pair.append([negative_index_pair[ii-1][1], negative_index_pair[ii][0]])
    segment_pair = np.asarray(segment_pair)
    ## based on data with each segment remove those segment with no current appplied
    index_to_remove = []
    for ii in range(0, len(segment_pair)):
        ele = segment_pair[ii]
        data_range = r_current_np[ele[0] : ele[1]]
        if np.mean(data_range) < 40:
            index_to_remove.append(ii)
    # remove 
    include_index = range(0, len(segment_pair))
    include_index = [x for i,x in enumerate(include_index) if i not in index_to_remove]   
    segment_pair_selected = segment_pair[include_index]
    
    if len(segment_pair_selected) == 1:
        segment_pair_selected = segment_pair
        
    
    ############################################################################
    ## alocate detected events to corrsponding windows
    events_within_partition = []
    for window in segment_pair_selected:
        start_bond = window[0]
        end_bond = window[1]
        temp = []
        for ele in event_index_pair:
            if ele[0] >= start_bond and ele[1] <= end_bond:
                temp.append(ele)
        events_within_partition.append(temp)
        
    if empty(events_within_partition):
        print('no event in this channel, continue')
        continue
        
    
    ############################################################################
    ## calcualte and write to csv
    channel_total_time = 0
    channel_total_event = 0
    channel_event_detial = []
    for ii in range(0, len(segment_pair_selected)):
        
        channel_total_time = channel_total_time + (segment_pair_selected[ii,1] - segment_pair_selected[ii,0])/sr
        #channel_total_event = channel_total_event + len(events_within_partition[ii]) 
        partition_start = segment_pair_selected[ii][0]
        ## each event detail
        ## 'event end time', 
        ## ' event width',
        ## 'event depth',
        ## 'event interval
        for jj in range(0,len(events_within_partition[ii])):
            
            event_start_time = events_within_partition[ii][jj][0]
            event_end_time = events_within_partition[ii][jj][1]
            event_width = (events_within_partition[ii][jj][1] - events_within_partition[ii][jj][0])/sr
            event_depth = np.mean(r_current_np[event_start_time : event_end_time])
             # calcualte intervals
            if jj == 0:
                event_interval = (event_start_time - partition_start)/sr
            else:
                event_interval = (events_within_partition[ii][jj][0] - events_within_partition[ii][jj-1][1])/sr
           #        0                 1               2            3            4
            temp = [event_start_time, event_end_time, event_width, event_depth, event_interval]
            
            ## do the selection
            if ((event_width >= width[0] and event_width <= width[1]) and (event_depth >= depth[0] and event_depth <= depth[1])):
                channel_total_event = channel_total_event + 1
                channel_event_detial.append(temp)
                all_channel_event_detail.append(temp)
                    
    channel_event_rate = channel_total_event/channel_total_time
    channel_event_detial = np.asarray(channel_event_detial)
    mean_width = np.mean(channel_event_detial[:,2])
    mean_depth = np.mean(channel_event_detial[:,3])
    std_width = np.std(channel_event_detial[:,2])
    std_depth = np.std(channel_event_detial[:,3])
    
    all_channel_total_time = all_channel_total_time + channel_total_time
    all_channel_total_event = all_channel_total_event + channel_total_event
    
    ## begin write to .csv file
    ### write down to CSV file
    # write down each event detail
    with open(file_path + '\\processed_data\\' + name + '_event_data_analysis.csv', 'a') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', 
                                quoting=csv.QUOTE_MINIMAL,
                                lineterminator='\r')
                            
        spamwriter.writerow(['file name', 
                         'event start time', 
                         'event end time', 
                         ' event width',
                         'event depth',
                         'event interval']);            
        for ele in channel_event_detial:
            spamwriter.writerow([name + '_' + channel_name, ele[0]/sr, ele[1]/sr, ele[2], ele[3], ele[4]])
        spamwriter.writerow(' ');  
    
    # write down each channel detail
    with open(file_path + '\\processed_data\\' + name + '_channel_data_analysis.csv', 'a') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', 
                                quoting=csv.QUOTE_MINIMAL,
                                lineterminator='\r')
                                
        spamwriter.writerow([name + '_' + channel_name, channel_total_event, channel_total_time, channel_total_event/channel_total_time])
        #spamwriter.writerow(' ');  

                
    ############################################################################
    ## plot and see
    fig1 = plt.figure(figsize=(25, 12))
        
    for ele in event_index_pair:
        #plt.axvline(data_event_start_index[ii] - data_event_length[ii] , color='r', linestyle='-')
        plt.axvline(ele[0], color='r', linestyle='-')
        plt.axvline(ele[1], color='b', linestyle='-')
    
    # for ele in negative_index_pair:
    #       plt.axvline(ele[0], color='r', linestyle='-')
    #       plt.axvline(ele[1], color='b', linestyle='-')
    
    # for ele in event_index_start:
    #     plt.axvline(ele, color='r', linestyle='-')
    #     
    # for ele in event_index_end:
    #     plt.axvline(ele, color='b', linestyle='-')
    
    for ele in segment_pair_selected:
        plt.axvspan(ele[0], ele[1], color='g', alpha=0.1)    
        
    plt.plot(r_current_np)
    ## save to file ##
    fig_path = file_path + '\\processed_data\\figs\\'
    fig_name = fig_path + name + '_' + channel_name +'.png'
    fig1.savefig(fig_name)
    
    
    ## plot histogram      
    fig2, axs = plt.subplots(2, 1, tight_layout=True, figsize=(25, 12))
    # plot width
    x = channel_event_detial[:,2]
    n_bins = int(bins_width)
    N, bins, patches = axs[0].hist(x, bins=n_bins)
    axs[0].set_xlabel('Time [s]', fontsize=12)
    axs[0].set_title("Width")
    
    y = channel_event_detial[:,3]
    n_bins = int(bins_depth)
    N, bins, patches = axs[1].hist(y, bins=n_bins)
    axs[1].set_xlabel('Voltage [mV]', fontsize=12)
    axs[1].set_title("Depth")
    
    fig_path = file_path + '\\processed_data\\figs\\'
    fig_name = fig_path + name + '_' + channel_name +'_histogram.png'
    fig2.savefig(fig_name)
    

if all_channel_total_event == 0:
    with open(file_path + '\\processed_data\\' + name + '_channel_data_analysis.csv', 'a') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', 
                                quoting=csv.QUOTE_MINIMAL,
                                lineterminator='\r')
        spamwriter.writerow('no evnets')   
else:
    
    # ### write down to CSV file
    with open(file_path + '\\processed_data\\' + name + '_channel_data_analysis.csv', 'a') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', 
                                quoting=csv.QUOTE_MINIMAL,
                                lineterminator='\r')
        
        spamwriter.writerow(['Total Events', 
                         'Total TIme', 
                         'Average Capture Time']);   
                                  
        
        spamwriter.writerow([all_channel_total_event, all_channel_total_time, all_channel_total_event/all_channel_total_time])
        spamwriter.writerow(' ');  
            
    ## plot histogram     
    all_channel_event_detail = np.asarray(all_channel_event_detail) 
    fig3, axs = plt.subplots(2, 1, tight_layout=True, figsize=(25, 12))
    # plot width
    x = all_channel_event_detail[:,2]
    n_bins = int(bins_width)
    N, bins, patches = axs[0].hist(x, bins=n_bins)
    axs[0].set_xlabel('Time [s]', fontsize=12)
    axs[0].set_title("Width")
        
    y = all_channel_event_detail[:,3]
    n_bins = int(bins_depth)
    N, bins, patches = axs[1].hist(y, bins=n_bins)
    axs[1].set_xlabel('Voltage [mV]', fontsize=12)
    axs[1].set_title("Depth")
        
    fig_path = file_path + '\\processed_data\\figs\\'
    fig_name = fig_path +'all_channel_histogram.png'
    fig3.savefig(fig_name)