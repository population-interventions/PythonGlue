
import math
import pandas as pd
import numpy as np

from matplotlib import pyplot
import matplotlib.ticker as ticker
import seaborn as sns

from utilities import OutputToFile
from utilities import ToHeatmap

def MakeFavouriteGraph(dataDir, measureCols):
    processDir = dataDir + '/ABM_process/'
    visualDir = dataDir + '/Graphs/'
    inputFile = processDir + 'infect_unique_weeklyAgg'
    
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(4 + len(measureCols))),
                     header=list(range(1)))
    
    df = df.drop(columns=['105.0']) # The last week is incomplete)
    df['0.0'] = df['0.0'] / 2.5
    df.index = df.index.droplevel(['run', 'global_transmissibility'])
    df = df.reorder_levels([1, 3, 4, 5, 6, 7, 0, 2], axis=0)
    df = df.sort_index()
    
    df = df / 7
    df = df.loc['ModerateSupress', 'No', 1.45, 0.95, 0.95, 2.5]
    print(df)
    
    df = df.unstack(['RolloutMonths'])
    df = df.reorder_levels([1, 0], axis=1)
    df = df[[0, 8, 12, 16]]
    df = df.reorder_levels([1, 0], axis=1)
    
    df = df.describe(percentiles=[0.05, 0.95])
    df = df.loc[['mean']].stack('RolloutMonths').transpose()
    df = df.reorder_levels([1, 0], axis=1)
    #df = df.droplevel(1, axis=1)
    df.columns = df.columns.rename('metric', 1)
    df.index = df.index.astype(float)
    df = df.sort_index(axis=0)
    df = df.sort_index(axis=1)
    
    df.plot()
    
def MakeStage0Graphs(dataDir, measureCols):
    processDir = dataDir + '/ABM_process/'
    visualDir = dataDir + '/Graphs/'
    inputFile = processDir + 'infect_unique_weeklyAgg'
    
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(4 + len(measureCols))),
                     header=list(range(1)))
    
    df = df.drop(columns=['0.0', '52.0']) # The last week is incomplete)
    df.index = df.index.droplevel(['run', 'global_transmissibility'])
    df = df.reorder_levels([1, 3, 4, 5, 6, 7, 0, 2], axis=0)
    df = df.sort_index()
    
    df = df / 7
    df = df.loc['None', 0, 1.3, 0.95, 0.95]
    
    df = df.unstack(['RolloutMonths', 'R0'])
    df = df.reorder_levels([1, 0, 2], axis=1)
    df = df[[0]]
    df = df.reorder_levels([1, 0, 2], axis=1)
    OutputToFile(df, visualDir + 'focus_data_in')
    
    df = df.describe(percentiles=[0.05, 0.95])
    df = df.loc[['mean', '50%', '95%', '5%']].stack('RolloutMonths').transpose()
    df = df.unstack('R0')
    df = df.reorder_levels([1, 0, 2], axis=1)
    #df = df.droplevel(1, axis=1)
    df.columns = df.columns.rename('metric', 1)
    df.index = df.index.astype(float)
    df = df.sort_index(axis=0)
    df = df.sort_index(axis=1)
    
    OutputToFile(df, visualDir + 'stage0_plot')


def MakeStage2Graphs(dataDir, measureCols):
    processDir = dataDir + '/ABM_process/'
    visualDir = dataDir + '/Graphs/'
    inputFile = processDir + 'infect_unique_weeklyAgg'
    
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(4 + len(measureCols))),
                     header=list(range(1)))
    
    df = df.drop(columns=['0.0', '105.0']) # The last week is incomplete)
    df.index = df.index.droplevel(['run', 'global_transmissibility'])
    df = df.reorder_levels([1, 3, 4, 5, 6, 7, 0, 2], axis=0)
    df = df.sort_index()
    
    df = df / 7
    df = df.loc['Stage2', 'Yes', 1.3, 0.95, 0.95]
    
    df = df.unstack(['RolloutMonths', 'R0'])
    df = df.reorder_levels([1, 0, 2], axis=1)
    df = df[[0, 12]]
    df = df.reorder_levels([1, 0, 2], axis=1)
    OutputToFile(df, visualDir + 'focus_data_in')
    
    df = df.describe(percentiles=[0.05, 0.95])
    df = df.loc[['mean', '50%', '95%', '5%']].stack('RolloutMonths').transpose()
    df = df.unstack('R0')
    df = df.reorder_levels([1, 0, 2], axis=1)
    #df = df.droplevel(1, axis=1)
    df.columns = df.columns.rename('metric', 1)
    df.index = df.index.astype(float)
    df = df.sort_index(axis=0)
    df = df.sort_index(axis=1)
    
    OutputToFile(df, visualDir + 'stage2_plot')


def MakeFullGraphs(dataDir, measureCols):
    processDir = dataDir + '/ABM_process/'
    visualDir = dataDir + '/Graphs/'
    inputFile = processDir + 'infect_unique_weeklyAgg'
    
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(4 + len(measureCols))),
                     header=list(range(1)))
    
    df = df.drop(columns=['0.0', '105.0']) # The last week is incomplete)
    df.index = df.index.droplevel(['run', 'global_transmissibility'])
    df = df.reorder_levels([1, 3, 4, 5, 6, 7, 0, 2], axis=0)
    df = df.sort_index()
    
    df = df / 7
    
    df = df.unstack(['RolloutMonths', 'VacKids'])
    OutputToFile(df, visualDir + 'focus_data_in')
    
    df = df.describe(percentiles=[0.05, 0.95])
    df = df.loc[['mean', '50%', '95%', '5%']].stack('RolloutMonths', 'VacKids').transpose()
    df = df.reorder_levels([1, 0], axis=1)
    df = df.unstack('VacKids')
    df.columns = df.columns.rename('metric', 1)
    df.index = df.index.astype(float)
    df = df.sort_index(axis=0)
    df = df.sort_index(axis=1)
    
    df.plot()
    
    OutputToFile(df, visualDir + 'fullGraphPlot')
