import csv
import matplotlib.pyplot as plt
import numpy as np
from pandas import DataFrame
import os
# import Tkinter, tkFileDialog
import fun
import pickle

file_path = os.path.dirname(os.path.realpath(__file__))

Fs = float(5000)

## load the detection summary
summary_path = file_path + '\\processed_data\\data_summary.txt'
with open(summary_path, 'rb') as fp:   # Unpickling
    summary_data = pickle.load(fp)
    
    
## ask for screening threshold for width and depth and width
width = input("Threshod for width in s: ")
print ("Threshod for width is set to " + width) 

depth = input("Threshod for depth in mV: ")
print ("Threshod for depth is set to " + depth) 

bins_width = input("Histogram bin number for width: ")
print ("Histogram bin number for width is set to: " + bins_width) 

bins_depth = input("Histogram bin number for depth: ")
print ("Histogram bin number for depth is set to: " + bins_depth) 

## summary_data structure
#each_file
#    each partition
         
#        [partition start, partition end, [[evnet window], start_current, end_current, start_time, width, depth]]
#                                           ....
#                                           .....

### write down to CSV file
with open(file_path + '\\processed_data\\' + 'data_analysis.csv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    #spamwriter.writerow('');  

## filter based on width, depth threshold
all_file_total_time = 0
all_file_total_event = 0
all_file_selected_events = []
all_file_name = []
for jj in range(0, len(summary_data)):
    
    name = summary_data[jj][0]
    all_file_name.append(name)
    
    file_total_time = 0
    file_total_event = 0
    file_selected_events = []
    
    for partition in summary_data[jj][1]:
        partition_start = partition[0]
        partition_end = partition[1]
        
        # addup total time
        file_total_time = file_total_time + (partition_end - partition_start)/Fs
        all_file_total_time = all_file_total_time + (partition_end - partition_start)/Fs
        
        events_in_partition = partition[2]
        
        for ii in  range(0, len(events_in_partition)):
            event_start = events_in_partition[ii][0][0]
            event_end = events_in_partition[ii][0][1]
            event_width = events_in_partition[ii][4]
            event_depth = events_in_partition[ii][5]
            
            # calcualte intervals
            if ii == 0:
                event_interval = (event_start - partition_start)/Fs
            else:
                event_interval = (events_in_partition[ii][0][0] - events_in_partition[ii-1][0][1])/Fs
                
            # file code, event start time, event endtime,  event width, event depth, event interval
            #      0            1            2             3            4            5
            temp = [jj, event_start/Fs, event_end/Fs, event_width, event_depth, event_interval]
            
            # do the selection
            if event_width >= float(width) and event_depth >= float(depth):
                all_file_selected_events.append(temp)
                file_selected_events.append(temp)
                file_total_event = file_total_event + 1
                all_file_total_event = all_file_total_event + 1
    file_cap_rate = file_total_event/file_total_time
    
    selected_events = np.asarray(file_selected_events)
    mean_width = np.mean(selected_events[:,3])
    mean_depth = np.mean(selected_events[:,4])
    std_width =  np.std(selected_events[:,3])
    std_depth = np.std(selected_events[:,4])
    
    ### write down to CSV file
    with open(file_path + '\\processed_data\\' + 'data_analysis.csv', 'a') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', 
                                quoting=csv.QUOTE_MINIMAL,
                                lineterminator='\r')
                                
        spamwriter.writerow([name + ' total time is : ' + str(file_total_time)]);  
        spamwriter.writerow([name +' total event is : ' + str(file_total_event)]);  
        spamwriter.writerow([name +' event rate is: ' + str(file_cap_rate)]);
        spamwriter.writerow([name +' mean width is: ' + str(mean_width)]);
        spamwriter.writerow([name +' mean depth is: ' + str(mean_depth)]);
        spamwriter.writerow([name +' width std is: ' + str(std_width)]);
        spamwriter.writerow([name +' depth std is: ' + str(std_depth)]);
        
        
        
        spamwriter.writerow(['file name', 
                         'event start time', 
                         'event end time', 
                         ' event width',
                         'event depth',
                         'event interval']);            
        for ele in file_selected_events:
            spamwriter.writerow([name, ele[1], ele[2], ele[3], ele[4], ele[5]])
        spamwriter.writerow(' ');  
    
    
    
all_file_cap_rate = all_file_total_event/all_file_total_time

## accumulate all to a single list of event and calcualte std, mean, histogram
# convert to python arrary
selected_events = np.asarray(all_file_selected_events)
mean_width = np.mean(selected_events[:,3])
mean_depth = np.mean(selected_events[:,4])
std_width =  np.std(selected_events[:,3])
std_depth = np.std(selected_events[:,4])

### write down to CSV file
with open(file_path + '\\processed_data\\' + 'data_analysis.csv', 'a') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', 
                            quoting=csv.QUOTE_MINIMAL,
                            lineterminator='\r')
    spamwriter.writerow(' ');  
    spamwriter.writerow(['Total time is : ' + str(all_file_total_time)]);  
    spamwriter.writerow(['Total event is : ' + str(all_file_total_event)]);  
    spamwriter.writerow(['Total event rate is: ' + str(all_file_cap_rate)]);

#### write down to CSV file
#with open(file_path + '\\processed_data\\' + 'data_analysis.csv', 'wb') as csvfile:
#    spamwriter = csv.writer(csvfile, delimiter=',',
#                               quotechar='|', quoting=csv.QUOTE_MINIMAL)
#                               
#    spamwriter.writerow(['Total time is : ' + str(all_file_total_time)]);  
#    spamwriter.writerow(['Total event is : ' + str(all_file_total_event)]);  
#    spamwriter.writerow(['event rate is: ' + str(all_file_cap_rate)]);
#      
#    spamwriter.writerow(['file no.', 
#                         'event start time', 
#                         'event end time', 
#                         ' event width',
#                         'event depth',
#                         'event interval']);            
#    for ele in selected_events:
#        spamwriter.writerow(ele)


## plot histogram      
fig, axs = plt.subplots(2, 1, tight_layout=True, figsize=(25, 12))

# plot width
x = selected_events[:,3]
n_bins = int(bins_width)
N, bins, patches = axs[0].hist(x, bins=n_bins)
axs[0].set_xlabel('Time [s]', fontsize=12)
axs[0].set_title("Width")


y = selected_events[:,4]
n_bins = int(bins_depth)
N, bins, patches = axs[1].hist(y, bins=n_bins)
axs[1].set_xlabel('Voltage [mV]', fontsize=12)
axs[1].set_title("Depth")

fig_path = file_path + '\\processed_data\\figs\\'
fig_name = fig_path + 'histogram.png'
fig.savefig(fig_name)

#plt.show()



