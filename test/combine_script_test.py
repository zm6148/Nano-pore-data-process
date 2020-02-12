import h5py
import pandas as pd
import numpy as np

filename = 'C:\\Users\\mz86\\Desktop\\Nanopore_v2\\iv curve.fast5'
f = h5py.File(filename, 'r')


# Obtain the dataset of references
n1 = f['Raw']
# Obtain the dataset pointed to by the first reference
ds = f[n1[0]]
# Obtain the data in ds
data = ds[:]
