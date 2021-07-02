
import math
import pandas as pd
import numpy as np

from utilities import OutputToFile
from utilities import ToHeatmap


def HeatmapProcess(df, heatmapStructure, dropMiddleValues=True):
    df = df.reset_index()
    df = ToHeatmap(df, heatmapStructure)
    
    if dropMiddleValues:
        df = df[df.index.get_level_values('Var_R0_mult') != 1.45]
        df = df.transpose()
        df = df[df.index.get_level_values('VacEfficacy') != 0.875]
        df = df.transpose()
    
    return df
    

def MakeInfectionHeatmap(name, aggType, heatmapStructure, outputFile, inputFile, measureCols, startWeek=13, window=26, dropMiddleValues=True):
    
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(2 + len(measureCols))),
                     header=list(range(1)))
    df = df.groupby(level=list(range(2, 2 + len(measureCols))), axis=0).mean()
    # Do (startWeek + 1) because week 0 consists of a single day, day 0.
    df = df[[str(i + startWeek + 1) + '.0' for i in range(window)]]
    df = df.transpose().describe().transpose()
    df = df[[aggType]] / 7
    df = df.rename(columns={aggType: name})

    df = HeatmapProcess(df, heatmapStructure, dropMiddleValues=dropMiddleValues)
    OutputToFile(df, outputFile)
    

def MakeStagesHeatmap(name, aggType, heatmapStructure, outputFile, inputFile, measureCols, stage_limit=2, startWeek=13, window=26, dropMiddleValues=True):
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(2 + len(measureCols))),
                     header=list(range(3)))
    df = df.apply(lambda c: [1 if x > stage_limit else 0 for x in c])
    df = df.groupby(level=list(range(2, 2 + len(measureCols))), axis=0).mean()
    
    df = df.droplevel([0, 2], axis=1)
    # Add 1 to the day because week 0 consists of a single day, day 0.
    df = df[[str(i + startWeek*7 + 1) for i in range(window*7)]]
    df = df.transpose().describe().transpose()
    df = df[[aggType]]
    df = df.rename(columns={aggType : name})
    
    df = HeatmapProcess(df, heatmapStructure, dropMiddleValues=dropMiddleValues)
    OutputToFile(df, outputFile)


def MakeHeatmaps(dataDir, measureCols, heatmapStructure, dropMiddleValues=True, windowSize=52, windowCount=2):
    processDir = dataDir + '/ABM_process/'
    visualDir = dataDir + '/ABM_heatmaps/'
    aggType = 'mean'
    
    print('Processing MakeInfectionHeatmap full')
    MakeInfectionHeatmap('full', aggType, heatmapStructure,
                         visualDir + 'infect_average_daily_full',
                         processDir + 'infect_unique_weeklyAgg',
                         measureCols,
                         startWeek=0, window=windowSize * windowCount,
                         dropMiddleValues=dropMiddleValues)
    print('Processing MakeStagesHeatmap stage full')
    MakeStagesHeatmap('full', aggType, heatmapStructure,
                      visualDir + 'lockdown_proportion_full',
                      processDir + 'processed_stage',
                      measureCols,stage_limit=0,
                         startWeek=0, window=windowSize * windowCount,
                         dropMiddleValues=dropMiddleValues)
    
    start = 0
    for i in range(windowCount):
        print('Processing ' + str(start) + '_to_' + str(start + windowSize))
        MakeInfectionHeatmap(str(start) + '_to_' + str(start + windowSize), aggType, heatmapStructure,
                             visualDir + 'infect_average_daily_' + str(start) + '_to_' + str(start + windowSize),
                             processDir + 'infect_unique_weeklyAgg',
                             measureCols,
                             startWeek=start, window=windowSize,
                             dropMiddleValues=dropMiddleValues)
        MakeStagesHeatmap(str(start) + '_to_' + str(start + windowSize), aggType, heatmapStructure,
                          visualDir + 'lockdown_proportion_' + str(start) + '_to_' + str(start + windowSize),
                          processDir + 'processed_stage',
                          measureCols,stage_limit=0,
                          startWeek=start, window=windowSize,
                          dropMiddleValues=dropMiddleValues)
        start = start + windowSize
