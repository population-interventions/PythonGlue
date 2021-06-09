# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 10:22:33 2021

@author: wilsonte
"""

import math
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import os

from utilities import SplitNetlogoList
from utilities import SplitNetlogoNestedList
from utilities import OutputToFile
from utilities import AddFiles
from utilities import ToHeatmap


def SplitOutDailyData(chunk, cohorts, days, name, filePath, fileAppend):
    columnName = name + '_listOut'
    df = SplitNetlogoNestedList(chunk, cohorts, days, columnName, name)
    OutputToFile(df, filePath + '_' + fileAppend)


def ProcessAbmChunk(chunk: pd.DataFrame, outputStaticData, filename,
                    measureCols_raw, indexRenameFunc, day_override=False):
    # Drop colums that are probably never useful.
    
    chunk = chunk[[
        '[run number]', 'rand_seed',
        'stage_listOut', 'scalephase', 'cumulativeInfected', 'casesReportedToday',
        'Deathcount', 'totalOverseasIncursions', 'infectNoVacArray_listOut', 'infectVacArray_listOut',
        'age_listOut', 'atsi_listOut', 'morbid_listOut'
    ] + measureCols_raw]
    
    cohorts = len(chunk.iloc[0].age_listOut.split(' '))
    days = len(chunk.iloc[0].stage_listOut.split(' '))
    if day_override:
        days = day_override
    
    if outputStaticData:
        staticData = pd.DataFrame(chunk[['age_listOut', 'atsi_listOut', 'morbid_listOut']].transpose()[0])
        staticData = SplitNetlogoList(staticData, cohorts, 0, '').transpose()
        staticData = staticData.rename(columns={'age_listOut': 'age', 'atsi_listOut': 'atsi', 'morbid_listOut': 'morbid'})
        OutputToFile(staticData, filename + '_static') 
    
    chunk = chunk.drop(['age_listOut', 'atsi_listOut', 'morbid_listOut'], axis=1)
    chunk = chunk.rename(mapper={'[run number]' : 'run'}, axis=1)
    chunk = chunk.set_index(['run', 'rand_seed',] + measureCols_raw)
    
    secondaryData = [
        'scalephase', 'cumulativeInfected', 'casesReportedToday',
        'Deathcount', 'totalOverseasIncursions'
    ]
    
    OutputToFile(chunk[secondaryData], filename + '_secondary')
    chunk = chunk.drop(secondaryData, axis=1)
    chunk = indexRenameFunc(chunk)
    
    SplitOutDailyData(chunk, 1, days, 'stage', filename, 'stage')
    SplitOutDailyData(chunk, cohorts, days, 'infectNoVacArray', filename, 'infectNoVac')
    SplitOutDailyData(chunk, cohorts, days, 'infectVacArray', filename, 'infectVac')


def ProcessAbmOutput(subfolder, indexRenameFunc, measureCols_raw, day_override=False):
    outputFile = subfolder + '/ABM_process/' + 'processed'
    filelist = [subfolder + '/ABM_out/' + 'MergedResults']
    chunksize = 4 ** 7
    
    firstProcess = True
    for filename in filelist:
        for chunk in tqdm(pd.read_csv(filename + '.csv', chunksize=chunksize, header=6), total=4):
            ProcessAbmChunk(chunk, firstProcess, outputFile, measureCols_raw,
                            indexRenameFunc, day_override=day_override)
            firstProcess = False


def ToVisualisation(chunk, filename, append, measureCols):
    chunk.columns.set_levels(chunk.columns.levels[1].astype(int), level=1, inplace=True)
    chunk.columns.set_levels(chunk.columns.levels[2].astype(int), level=2, inplace=True)
    chunk = chunk.groupby(level=[0, 1], axis=1).sum()
    chunk.sort_values('day', axis=1, inplace=True)
    
    index = chunk.columns.to_frame()
    index['week'] = np.floor((index['day'] + 6)/7)
    
    chunk.columns = index
    chunk.columns = pd.MultiIndex.from_tuples(chunk.columns, names=['metric', 'day', 'week'])
    chunk.columns = chunk.columns.droplevel(level=0)
    chunk = chunk.groupby(level=[1], axis=1).sum()
    
    OutputToFile(chunk, filename + '_' + append + '_weeklyAgg')
    

def ToVisualisationRollingWeekly(chunk, filename, append):
    chunk.columns.set_levels(chunk.columns.levels[1].astype(int), level=1, inplace=True)
    chunk.columns.set_levels(chunk.columns.levels[2].astype(int), level=2, inplace=True)
    chunk = chunk.groupby(level=[0, 1], axis=1).sum()
    chunk.columns = chunk.columns.droplevel(level=0)
    
    leftPad = [-(i+1) for i in range(6)]
    for v in leftPad:
        chunk[v] = 0
    chunk.sort_values('day', axis=1, inplace=True)
    chunk = chunk.rolling(7, axis=1).mean()
    chunk = chunk.drop(columns = leftPad)
    
    OutputToFile(chunk, filename + '_' + append + '_rolling_weekly')


def ProcessFileToVisualisation(subfolder, append, measureCols):
    chunksize = 4 ** 7
    filename = subfolder + '/ABM_process/' + 'processed'
    for chunk in tqdm(pd.read_csv(filename + '_' + append + '.csv', chunksize=chunksize,
                                  index_col=list(range(2 + len(measureCols))),
                                  header=list(range(3)),
                                  dtype={'day' : int, 'cohort' : int}),
                      total=4):
        ToVisualisation(chunk, filename, append, measureCols)

    
def DoAbmProcessing(dataDir, indexRenameFunc, measureCols, measureCols_raw, day_override=False):
    print('Processing ABM Output', dataDir)
    ProcessAbmOutput(dataDir, indexRenameFunc, measureCols_raw, day_override=day_override)
    
    print('Processing infectNoVac')
    ProcessFileToVisualisation(dataDir, 'infectNoVac', measureCols) 
    print('Processing infectVac')
    ProcessFileToVisualisation(dataDir, 'infectVac', measureCols)
    AddFiles(dataDir + '/ABM_process/' + 'infect_unique_weeklyAgg',
        [
            dataDir + '/ABM_process/' + 'processed_infectNoVac_weeklyAgg',
            dataDir + '/ABM_process/' + 'processed_infectVac_weeklyAgg',
        ],
        index=(2 + len(measureCols))
    )
    ProcessFileToVisualisation(dataDir, 'stage', measureCols)

