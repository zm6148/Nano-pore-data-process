#this gets raw data from a bulk fast5 and exports it into a .csv. 
#You have to select which channels you want, and edit the fast5 path and the output
#option to add additional columns with set values

#import
from fast5_research.fast5_bulk import BulkFast5
import pandas as pd
import csv
import numpy as np
from pandas import DataFrame
import os
from tkinter import *
import pickle

file_path = os.path.dirname(os.path.realpath(__file__))
filepath = file_path + "\\iv curve.fast5"
print (filepath)
f = BulkFast5(filepath)
print ("got fast5")

#select channels
channels = (22, 442)
#channels = range(1,513)
print ("selected channels")
#get raw and add channel column
r = pd.DataFrame()
for i in channels:	
    data = pd.DataFrame(f.get_raw(i))
    data['channel'] = i
    data['sample'] = range(len(data))
    data.columns = ['current', 'channel', 'sample']
    r = r.append(data)
print ("got raw")

#get time
sr = f.sample_rate
r['time'] =  r['sample']/sr # add time column
print ("added time column")

#add condition column
#r['condition'] = "value"
#print "added condition column" 

#export
r.to_csv(file_path + "\\output.csv", index=False)
print ("finished")
