import csv
import matplotlib.pyplot as plt
import numpy as np
from pandas import DataFrame
import os
# import tkinter
# from tkinter import filedialog
import fun

def find_events(data, start_index, end_index, multiply, thr_low, thr_high):
    
    ############################################################################
    ## update the thresholds based on data from start to end
    if (data[start_index,1] - data[0,1] > 5 * thr_high):
        data_partitioned = data[0 : start_index, 1]
    else: 
        data_partitioned = data[end_index : -1, 1]
    
    ## calcualte slop
    slop = data[1:,1] - data[:-1,1]
    
    ################################################################################
    ## find the noise floor from the partitioned data
    theta=np.median(np.absolute(data_partitioned)/0.6745)
    thr_low = -5*theta
    thr_high = 5*theta
    
    ################################################################################
    ## remove all slop data within that exclusion rage
    ## the rest could be the edge of the current step
    slop_change_index = []
    for ii in range(0,len(slop)):
        if ((slop[ii] < thr_low) or (slop[ii] > thr_high)):
            slop_change_index.append(ii)
    
    ################################################################################
    ## remove not current event 
    ## remove all slop data that its corresponding real data is only a peak (no gapwidth)
    ## use the slop peak index back in the real data index
    ## if in real data value before and after are witih noise floor remove this index
    real_edge_index_negaive_slop = []
    real_edge_index_positive_slop = []
    
    for ele in slop_change_index:
        diff = abs(data[ele+1-1,1]) - abs(data[ele+1+1,1])
        #diff = abs(np.median(data[ele+1-10:ele+1,1])) - abs(np.median(data[ele+1:ele+1+10,1]))
        
        if ((abs(diff)  > multiply * thr_high)) and slop[ele] < 0:
            real_edge_index_negaive_slop.append(ele)
            
        if ((abs(diff)  > multiply * thr_high)) and slop[ele] > 0:
            real_edge_index_positive_slop.append(ele+1)     
        #if  slop[ele] < thr_low:
        #    real_edge_index_negaive_slop.append(ele)
        #    
        #if  slop[ele] >= thr_high:
        #    real_edge_index_positive_slop.append(ele)
            
        #if slop[ele] < 0:
        #    real_edge_index_negaive_slop.append(ele)
        #    
        #if slop[ele] >= 0:
        #    real_edge_index_positive_slop.append(ele)
                
                
    ################################################################################
    ## remove too close point for negative
    index_to_remove = []
    for ii in range(1, len(real_edge_index_negaive_slop)):
        diff = real_edge_index_negaive_slop[ii] -real_edge_index_negaive_slop[ii-1]
        if diff <= 1:
            index_to_remove.append(ii)
    ## delete too close index     
    for index in sorted(index_to_remove, reverse=True):
        del real_edge_index_negaive_slop[index]
        
    ## remove too close point for positive
    index_to_remove = []
    for ii in range(1, len(real_edge_index_positive_slop)):
        diff = real_edge_index_positive_slop[ii] -real_edge_index_positive_slop[ii-1]
        if diff <= 1:
            index_to_remove.append(ii)
    ## delete too close index     
    for index in sorted(index_to_remove, reverse=True):
        del real_edge_index_positive_slop[index]
    
    
    ################################################################################
    ## put two arrays togeter
    combined_event_index = [];
    # append to combined_event_index 
    for ele in real_edge_index_negaive_slop:
        combined_event_index.append([ele,-1])
    for ele in real_edge_index_positive_slop:
        combined_event_index.append([ele,1])
    combined_event_index = np.asarray(combined_event_index)
    
    return combined_event_index, real_edge_index_negaive_slop, real_edge_index_positive_slop, thr_low, thr_high

def find_events_pairs(combined_event_index):
    
    
    # sort by first column
    combined_event_index_sorted = combined_event_index[combined_event_index[:, 0].argsort()]
    # remove to closed ones
    #index_to_remove = []
    #for ii in range(1, len(combined_event_index_sorted)):
    #    diff = combined_event_index_sorted[ii,0] - combined_event_index_sorted[ii-1,0]
    #    if diff <= 1:
    #        index_to_remove.append(ii)
    ## delete too close index     
    combined_event_index_new = combined_event_index_sorted
        
    ################################################################################
    ## pair one - with anohter + to form current event index pair
    left = 0
    right = left + 1
    event_index_pair = []
    while right < len(combined_event_index_new):
        if combined_event_index_new[left, 1] == -1 and combined_event_index_new[right, 1] == 1 and right - left == 1:
            event_index_pair.append([combined_event_index_new[left, 0], combined_event_index_new[right, 0]])
            left = right + 1
            right = right + 2
        elif combined_event_index_new[left, 1] == -1 and combined_event_index_new[right, 1] == -1:
            right = right + 1
        elif combined_event_index_new[left, 1] == -1 and combined_event_index_new[right, 1] == 1:
            event_index_pair.append([combined_event_index_new[right - 1, 0], combined_event_index_new[right, 0]])
            left = right + 1
            right = right + 2
        else:
            left = left + 1
            right = right + 1
    
    #run = []
    #result = [run]
    #for ii in range(0, len(combined_event_index_new)):
    #    if combined_event_index_new[ii,1] == -1:
    #        run.append(ii)
    #    else:
    #        result.append(run)
    #        run = []
    #            
    #c_positive = filter(None,result)
    ##c_positive = c_positive[0:-1-1]   
    ## event pair
    #event_index_pair = []
    #for ele in c_positive:
    #    if len(ele) == 1:
    #        temp = [combined_event_index_new[ele[0], 0], combined_event_index_new[ele[0]+1, 0]]
    #    else:
    #        temp = [combined_event_index_new[ele[-1], 0], combined_event_index_new[ele[-1]+1,0]]
    #    event_index_pair.append(temp)
        
    ## thoese index are the gap index
    # event_index_pair.pop(0)
    return event_index_pair
    
    
    
def partition(data, thr_low, thr_high):
    
    above_thr_index_all = []
    for ii in range(0,len(data)):
        if (data[ii] > 10 * thr_high):
            above_thr_index_all.append(ii)
      
    ## find start and end
    start_index = above_thr_index_all[0]
    end_index = above_thr_index_all[-1]
    
    ## find negative current begin and end pair
    negative_index_all = []
    negative_index_pair = []
    
    for ii in range(start_index, end_index+1):
         if (data[ii] < 3 * thr_low) :
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
        
    
    ############################################################################
    ## first partition the data based on negative currents
    left = start_index
    right = left + 1
    first_partition_start_end_index = []
    ii = 0
    while right < end_index:
        if ii > len(negative_index_pair)-1:
            first_partition_start_end_index.append([negative_index_pair[ii-1][1], end_index])
            break
        elif right == negative_index_pair[ii][0]:
            first_partition_start_end_index.append([left, right])
            left = negative_index_pair[ii][1]
            right = left + 1
            ii = ii + 1
        else:
            right = right + 1
    return first_partition_start_end_index, start_index, end_index, negative_index_pair
    

def partition2(data, thr_low, thr_high):
    

    ##  find region where no applied current
    # no_event_period_index = []
    # for ii in range(0, len(data)-100):
    #     window = data[ii : ii + 100]
    #     if np.median(window) < 10 * thr_high:
    #         no_event_period_index.append(ii)
        
    ## find negative current begin and end pair
    negative_index_all = []
    negative_index_pair = []
    
    for ii in range(0, len(data)):
         if (data[ii] < thr_low) :
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
    

    return negative_index_pair



