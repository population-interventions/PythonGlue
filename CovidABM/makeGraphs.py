
import math
import pandas as pd
import numpy as np

from matplotlib import pyplot
import matplotlib.ticker as ticker
import seaborn as sns

from utilities import OutputToFile
from utilities import ToHeatmap

def MakeGraphs(dataDir, measureCols):
    processDir = dataDir + '/ABM_process/'
    visualDir = dataDir + '/Graphs/'
    inputFile = processDir + 'infect_unique_weeklyAgg'
    
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(4 + len(measureCols))),
                     header=list(range(1)))
    
    df = df.drop(columns='105.0') # The last week is incomplete)
    df.index = df.index.droplevel(['run', 'global_transmissibility'])
    df = df.reorder_levels([1, 3, 4, 5, 6, 7, 0, 2], axis=0)
    df = df.sort_index()
    
    df = df.loc['ModerateSupress', 'No', 1.3, 0.95, 0.95, 2.5]
    
    df = df.unstack('RolloutMonths')
    df = df.describe(percentiles=[0.05, 0.95])
    df = df.loc[['50%', '5%', '95%']].stack('RolloutMonths').transpose()
    df = df.reorder_levels([1, 0], axis=1)
    df = df.sort_index(axis=1)
    
    df[0].plot()
    df[8].plot()
    df[12].plot()
    df[16].plot()
    
    OutputToFile(df, visualDir + 'focus_scenario')