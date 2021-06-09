
import math
import pandas as pd
import numpy as np

from matplotlib import pyplot
import matplotlib.ticker as ticker
import seaborn as sns

from utilities import OutputToFile
from utilities import ToHeatmap

def MakeFavouriteGraph(dataDir, dataName, measureCols, favParams, median=True, mean=True, si=False):
    processDir = dataDir + '/ABM_process/'
    visualDir = dataDir + '/Graphs/'
    inputFile = processDir + dataName + '_weeklyAgg'
    
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(2 + len(measureCols))),
                     header=list(range(1)))
    
    df = df.drop(columns=['105.0']) # The last week is incomplete)
    df['0.0'] = df['0.0'] / 2.5
    df.index = df.index.droplevel(['run'])
    df = df.reorder_levels([1, 2, 3, 4, 5, 0], axis=0)
    df = df.sort_index()
    
    df = df / 7
    for val in favParams:
        df = df.loc[val] 
    
    df = df.describe(percentiles=[0.05, 0.95])
    
    metrics = []
    if median:
        metrics += ['50%']
    if mean:
        metrics += ['mean']
    if si:
        metrics += ['5%', '95%']
        
    df = df.loc[metrics].transpose()
    
    df.plot()
    

def MakeFullGraphs(dataDir, dataName, measureCols, splitParam, median=True, mean=True, si=False):
    processDir = dataDir + '/ABM_process/'
    visualDir = dataDir + '/Graphs/'
    inputFile = processDir + dataName + '_weeklyAgg'
    
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(2 + len(measureCols))),
                     header=list(range(1)))
    
    df = df.drop(columns=['0.0', '105.0']) # The last week is incomplete)
    df.index = df.index.droplevel(['run'])
    df = df.reorder_levels([1, 3, 4, 5, 0, 2], axis=0)
    df = df.sort_index()
    
    df = df / 7
    
    df = df.unstack([splitParam])
    OutputToFile(df, visualDir + 'focus_data_in')
    
    metrics = []
    if median:
        metrics += ['50%']
    if mean:
        metrics += ['mean']
    if si:
        metrics += ['5%', '95%']
        
    df = df.describe(percentiles=[0.05, 0.95])
    df = df.loc[metrics].stack(splitParam).transpose()
    df.index = df.index.astype(float)
    df = df.sort_index(axis=0)
    df = df.sort_index(axis=1)
    
    df.plot()
    #OutputToFile(df, visualDir + dataName + 'fullGraphPlot')
