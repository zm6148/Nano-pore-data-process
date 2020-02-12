#this gets raw data from a bulk fast5 and exports it into a .csv. 
#You have to select which channels you want, and edit the fast5 path and the output
#option to add additional columns with set values

#import
import warnings
from fast5_research.fast5_bulk import BulkFast5
import pandas as pd
import csv
import numpy as np
from pandas import DataFrame
import os
from tkinter import filedialog
import tkinter as tk
import pickle
import matplotlib.pyplot as plt
import fun
from scipy import signal

warnings.filterwarnings('ignore', category=DeprecationWarning)

## ask for which fast5 file to process
file_path = os.path.dirname(os.path.realpath(__file__))
root = tk.Tk()
root.withdraw()
file_name = filedialog.askopenfilename(parent=root, initialdir=file_path + "\\fast5_data", title='Please select the fast5 file to process')
print (file_name + " selected.")
## load selected file
f = BulkFast5(file_name)

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
    
print("Begin Extraction")

## loop through all the channls and do detection
extracted_file_path = file_path + "\\extracted_channel_data"
for channel in channels:
    extracted_file_name = file_name.split("/")[-1] + "_channel_" + str(channel) + '.csv'
    print("Extracting " + extracted_file_name)
    #get raw and add channel column
    r = pd.DataFrame()
    data = pd.DataFrame(f.get_raw(channel))
    data['channel'] = channel
    data['sample'] = range(len(data))
    data.columns = ['current', 'channel', 'sample']
    r = r.append(data)
   
    #get time
    sr = f.sample_rate
    r['time'] =  r['sample']/sr # add time column
    
    #export
    r.to_csv(extracted_file_path + "\\" + extracted_file_name, index=False)
    
print ("All channel(s) extracted, begin detection.")

################################################################################
## begin detection ##
################################################################################

## directory is already known

dirname = file_path + "\\extracted_channel_data"
filename_list=[]


## this is the list of the
## list of list has the window start and end list and all the events in
## in this window
## [[[window], [events]], [[window], [events]], ......]]]
all_file_events = []

for filename in os.listdir(dirname):
    
    ##
    print('processing ' + filename)

    ############################################################################
    ## open CSV data file
    with open(dirname + '\\' + filename, 'r') as csvfile:
        data_o = list(csv.reader(csvfile))
    ## convert to numpy array
    data_o = np.asarray(data_o)
    data_o = data_o[1:,:].astype(np.float)
    
    ## data[:,0] time 
    ## data[:,1] votage value
    ## rearrange data colum
    data = np.column_stack((data_o[:,3], data_o[:,0]))
    
    ## calcualte Fs
    Fs = 1/(data[1,0] - data[0,0])
    blockage_threshold = 5 #in seconds
    
    # ## filter data
    # #Creation of the filter
    # cutOff = 500 # Cutoff frequency
    # nyq = 0.5 * Fs
    # N  = 6    # Filter order
    # fc = cutOff / nyq # Cutoff frequency normal
    # b, a = signal.butter(N, fc)
    # 
    # data_filtered = signal.filtfilt(b,a, data[:,1])
    # 
    # data = np.column_stack((data_o[:,3], data_filtered))
    
    
    ################################################################################
    ## find the slope of change o the entire recording
    slop = data[1:,1] - data[:-1,1]
    
    
    ################################################################################
    ## find the noise floor from the slope data
    theta=np.median(np.absolute(slop)/0.6745)
    thr_low = -5*theta
    thr_high = 5*theta
    
    ## continue with next channel if there is no event to be found
    if max(data[:,1]) < 15 * thr_high:
        print("no event in " + filename + ", moving on")
        continue
    
    ############################################################################
    ## section the data first using the threshold obtained from slop
    first_partition_start_end_index, start_index, end_index, negative_index_pair = fun.partition(data, thr_low, thr_high)
    
    
    ############################################################################
    ## find all event index pair
    multiply = 20
    combined_event_index, real_edge_index_negaive_slop, real_edge_index_positive_slop, thr_low, thr_high = fun.find_events(data, start_index, end_index, multiply, thr_low, thr_high)
    
    while (len(combined_event_index) < 4 and multiply >0):    
        multiply = multiply - 10
        combined_event_index, real_edge_index_negaive_slop, real_edge_index_positive_slop, thr_low, thr_high = fun.find_events(data, start_index, end_index, multiply, thr_low, thr_high)
        
    if (len(combined_event_index) >= 4):
        event_index_pair = fun.find_events_pairs(combined_event_index)
    else: 
        continue
               
    ############################################################################
    ## find the real_edge_index_negaive_slop that is not covered in the event pairs
    a = np.asarray(event_index_pair)
    b = real_edge_index_negaive_slop
    leftover_dropofcurrent = [x for x in b if x not in a[:,0]]
     
    ############################################################################
    ## find the blockage event based on the threshold for blockage
    blockage_index_pair = []
    index_to_remove_from_event = []
    for ii in range(0, len(event_index_pair)):
        if ((event_index_pair[ii][1] - event_index_pair[ii][0])/Fs > blockage_threshold):
            blockage_index_pair.append(event_index_pair[ii])
            index_to_remove_from_event.append(ii)
    for ele in index_to_remove_from_event: 
        event_index_pair.pop(ele)
        
    ############################################################################
    ## for each of the first partition data divide further by blockage or 
    ## leftoverdropofcurrent
    further_partition_start_end_pair = []
    for ele in first_partition_start_end_index:
        left = ele[0]
        right = left + 1
        while 1:
            #print(right)
            if len(blockage_index_pair) and right == blockage_index_pair[0][0]  > 0:
                further_partition_start_end_pair.append([left,right])
                left = blockage_index_pair[0][1]
                right = left + 1
                blockage_index_pair.pop(0)
            elif len(leftover_dropofcurrent) and right == leftover_dropofcurrent[0] > 0:
                further_partition_start_end_pair.append([left,right])
                left = leftover_dropofcurrent[0]
                right = left + 1
                leftover_dropofcurrent.pop(0)     
                break         
            elif right == ele[1]:
                further_partition_start_end_pair.append([left,right])
                break
            else:
                right = right + 1
     
    ############################################################################
    ## alocate detected events to corrsponding windows
    events_within_partition = []
    for window in further_partition_start_end_pair:
        start_bond = window[0]
        end_bond = window[1]
        temp = []
        for ele in event_index_pair:
            if ele[0] >= start_bond and ele[1] <= end_bond:
                temp.append(ele)
        events_within_partition.append(temp)
   
   
    ############################################################################
    ## calcualte rate and 
    ## write to .csv
    all_partition_event_data = []
    for ii in range(0, len(events_within_partition)):
        section_window = further_partition_start_end_pair[ii]
        partition_event_data = []
        for ele in events_within_partition[ii]:
            start_current = np.median(data[ele[0]-100:ele[0], 1])
            end_current = np.median(data[ele[1]:ele[1]+100, 1])
            start_time = data[ele[0], 0]
            width = (ele[1] - ele[0])/Fs
            depth = start_current - np.mean(data[ele[0]:ele[1], 1])
            temp = [ele, start_current, end_current, start_time, width, depth]
            partition_event_data.append(temp)
        section_window.append(partition_event_data)
        all_partition_event_data.append(section_window)  
    all_file_events.append([filename,all_partition_event_data])
    
    #final_output = []
    #for ele in event_index_pair:
    #    start_current = np.median(data[ele[0]-100:ele[0], 1])
    #    end_current = np.median(data[ele[1]:ele[1]+100, 1])
    #    start_time = data[ele[0], 0]
    #    width = (ele[1] - ele[0])/Fs
    #    depth = np.mean(data[ele[0]:ele[1], 1])
    #    final_output.append([start_current, end_current, start_time, width, depth])
    #final_output = np.asarray(final_output)
    #    
    ### features
    #start_current = final_output[:, 0]
    #end_current = final_output[:, 1]
    #width = final_output[:, 2]
    #depth = final_output[:, 3]
    #
    ### calcualte event rate
    #total_duration = 0
    #for ele in further_partition_start_end_pair:
    #    partition_duration = (ele[1] - ele[0]) / Fs
    #    total_duration = total_duration + partition_duration
    #total_event = len(event_index_pair)
    #rate = total_event / total_duration
    #
    #
    #############################################################################
    ### write down to CSV file
    #with open(file_path + '\\processed_data\\' + filename, 'wb') as csvfile:
    #    spamwriter = csv.writer(csvfile, delimiter=',',
    #                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    #    spamwriter.writerow(['event rate is: ' + str(rate)]);  
    #    spamwriter.writerow(['start_current', 'end_current', 'start_time', 'width', 'depth']);            
    #    for ele in final_output:
    #        spamwriter.writerow(ele)
            
    
    ################################################################################
    ## plot and see
    
    fig = plt.figure(filename, figsize=(25, 12))
    
    #plt.axhline(y=thr_low, color='r', linestyle='-')
    #plt.axhline(y=thr_high, color='r', linestyle='-')
    
    #for ele in real_edge_index_negaive_slop:
    #    plt.axvline(x=ele, color='k', linestyle='-')
    #for ele in real_edge_index_positive_slop:
    #    plt.axvline(x=ele, color='k', linestyle='-')
    
    #for ele in combined_event_index_new:
    #    if ele[-1] == -1:
    #        plt.axvline(x=ele[0], color='r', linestyle='-')
    #    else:
    #        plt.axvline(x=ele[0], color='b', linestyle='-')
    #
    #for ele in combined_event_index_new:
    #    if ele[1] == -1:
    #        plt.axvline(x=ele[0], color='r', linestyle='-')
    #    else:
    #        plt.axvline(x=ele[0], color='b', linestyle='-')
    
    #for ele in negative_index_all:
    #    plt.axvline(x=ele, color='r', linestyle='-')
    
    #for ele in negative_index_pair:
    #    plt.axvline(x=ele[0], color='r', linestyle='-')
    #    plt.axvline(x=ele[1], color='b', linestyle='-')
    
#    for ele in first_partition_start_end_index:
#        plt.axvline(x=ele[0], color='y', linestyle='-')
#        plt.axvline(x=ele[1], color='y', linestyle='-')
#
    #for ele in event_index_pair:
    #    plt.axvline(x=ele[0], color='r', linestyle='-')
    #    plt.axvline(x=ele[1], color='b', linestyle='-')
#    
#    for ele in leftover_dropofcurrent:
#        plt.axvline(x=ele, color='k', linestyle='-')

    for ele in further_partition_start_end_pair:
        plt.axvspan(ele[0] - start_index, ele[1] - start_index, color='g', alpha=0.1)
    
    for section in events_within_partition:
        for ele in section:
            plt.axvline(x=ele[0] - start_index, color='r', linestyle='-')
            plt.axvline(x=ele[1] - start_index, color='b', linestyle='-')
                    
    #plt.plot(slop)   
    #plt.plot(data[:,1])
    plt.plot(data[start_index: end_index,1])
    #plt.show()
    
    #if len(blockage_index_pair) > 0:
    #    for ele in blockage_index_pair:
    #        plt.axvline(x=ele[0], color='k', linestyle='-')
    #        plt.axvline(x=ele[1], color='k', linestyle='-')
    
    ## save to file ##
    fig_path = file_path + '\\processed_data\\figs\\'
    fig_name = fig_path + filename +'.png'
    fig.savefig(fig_name)
    

############################################################################
## save summary data
with open(file_path + '\\processed_data\\data_summary.txt', 'wb') as fp:   #Pickling
    pickle.dump(all_file_events, fp)
print('Done')
