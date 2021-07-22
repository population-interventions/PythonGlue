# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 10:22:33 2021

@author: wilsonte
"""

import math
import pandas as pd
import numpy as np
from tqdm import tqdm
import pathlib
import time
import os

from utilities import SplitNetlogoList
from utilities import SplitNetlogoNestedList
from utilities import OutputToFile
from utilities import AddFiles
from utilities import ToHeatmap


def SplitOutDailyData(chunk, cohorts, days, name, filePath, fileAppend, fillTo=False):
    columnName = name + '_listOut'
    df = SplitNetlogoNestedList(chunk, cohorts, days, columnName, name, fillTo=fillTo)
    OutputToFile(df, filePath + '_' + fileAppend)


def ProcessAbmChunk(chunk: pd.DataFrame, outputStaticData, filename,
                    measureCols_raw, indexRenameFunc, day_override=False):
    # Drop colums that are probably never useful.
    
    chunk = chunk[[
        '[run number]', 'rand_seed',
        'stage_listOut', 'scalephase', 'cumulativeInfected',
        'infectNoVacArray_listOut', 'infectVacArray_listOut',
        'case_listOut', 'case7_listOut',
        'case14_listOut', 'case28_listOut',
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
        'scalephase', 'cumulativeInfected',
    ]
    
    OutputToFile(chunk[secondaryData], filename + '_secondary')
    chunk = chunk.drop(secondaryData, axis=1)
    chunk = indexRenameFunc(chunk)
    
    SplitOutDailyData(chunk, 1, days, 'case', filename, 'case', fillTo=day_override)
    SplitOutDailyData(chunk, 1, days, 'case7', filename, 'case7', fillTo=day_override)
    SplitOutDailyData(chunk, 1, days, 'case14', filename, 'case14', fillTo=day_override)
    SplitOutDailyData(chunk, 1, days, 'stage', filename, 'stage', fillTo=day_override)
    SplitOutDailyData(chunk, cohorts, days, 'infectNoVacArray', filename, 'infectNoVac', fillTo=day_override)
    SplitOutDailyData(chunk, cohorts, days, 'infectVacArray', filename, 'infectVac', fillTo=day_override)


def ProcessAbmOutput(subfolder, indexRenameFunc, measureCols_raw, day_override=False):
    outputFile = subfolder + '/ABM_process/' + 'processed'
    inputPath = pathlib.Path(subfolder + '/ABM_out/')
    suffix = '.csv'
    pathList = sorted(inputPath.glob('*{}'.format(suffix)))
    filelist = [] # TODO - Do better.
    for path in pathList:
        filelist.append(subfolder + '/ABM_out/' + str(path.name)[:-len(suffix)] )
        
    print("Processing Files", filelist)
    chunksize = 4 ** 7
    firstProcess = True
    for filename in filelist:
        for chunk in tqdm(pd.read_csv(filename + '.csv', chunksize=chunksize, header=6), total=4):
            ProcessAbmChunk(chunk, firstProcess, outputFile, measureCols_raw,
                            indexRenameFunc, day_override=day_override)
            firstProcess = False


def ToVisualisation(chunk, filename, append, measureCols, divisor=False, dayStartOffset=0, outputDay=False):
    chunk.columns.set_levels(chunk.columns.levels[1].astype(int), level=1, inplace=True)
    chunk.columns.set_levels(chunk.columns.levels[2].astype(int), level=2, inplace=True)
    chunk = chunk.groupby(level=[0, 1], axis=1).sum()
    chunk.sort_values('day', axis=1, inplace=True)
    if divisor:
        chunk = chunk / divisor
    
    if outputDay:
        chunk_day = chunk.copy()
        chunk_day.columns = chunk_day.columns.droplevel(level=0)
        OutputToFile(chunk_day, filename + '_' + append + '_daily')
        
    index = chunk.columns.to_frame()
    index['week'] = np.floor((index['day'] - dayStartOffset)/7)
    
    chunk.columns = index
    chunk.columns = pd.MultiIndex.from_tuples(chunk.columns, names=['metric', 'day', 'week'])
    chunk.columns = chunk.columns.droplevel(level=0)
    chunk = chunk.groupby(level=[1], axis=1).sum()
    
    OutputToFile(chunk, filename + '_' + append + '_weeklyAgg')


def ProcessFileToVisualisation(subfolder, append, measureCols, divisor=False, dayStartOffset=None, outputDay=False):
    chunksize = 4 ** 7
    filename = subfolder + '/ABM_process/' + 'processed'
    for chunk in tqdm(pd.read_csv(filename + '_' + append + '.csv', chunksize=chunksize,
                                  index_col=list(range(2 + len(measureCols))),
                                  header=list(range(3)),
                                  dtype={'day' : int, 'cohort' : int}),
                      total=4):
        ToVisualisation(chunk, filename, append, measureCols, divisor=divisor, dayStartOffset=dayStartOffset, outputDay=outputDay)


def InfectionsAndStageVisualise(dataDir, measureCols, dayStartOffset=0):
    print('Processing infectNoVac')
    ProcessFileToVisualisation(dataDir, 'infectNoVac', measureCols, dayStartOffset=dayStartOffset) 
    print('Processing infectVac')
    ProcessFileToVisualisation(dataDir, 'infectVac', measureCols, dayStartOffset=dayStartOffset)
    AddFiles(dataDir + '/ABM_process/' + 'infect_unique_weeklyAgg',
        [
            dataDir + '/ABM_process/' + 'processed_infectNoVac_weeklyAgg',
            dataDir + '/ABM_process/' + 'processed_infectVac_weeklyAgg',
        ],
        index=(2 + len(measureCols))
    )
    ProcessFileToVisualisation(dataDir, 'stage', measureCols, dayStartOffset=dayStartOffset)


def CasesVisualise(dataDir, measureCols, dayStartOffset=0):
    print('Processing cases')
    ProcessFileToVisualisation(dataDir, 'case', measureCols, divisor=False, dayStartOffset=dayStartOffset, outputDay=True) 
    ProcessFileToVisualisation(dataDir, 'case7', measureCols, divisor=7, dayStartOffset=dayStartOffset, outputDay=True) 
    ProcessFileToVisualisation(dataDir, 'case14', measureCols, divisor=14, dayStartOffset=dayStartOffset, outputDay=True) 


def DoAbmProcessing(dataDir, indexRenameFunc, measureCols, measureCols_raw, day_override=False, dayStartOffset=0):
    print('Processing ABM Output', dataDir)
    ProcessAbmOutput(dataDir, indexRenameFunc, measureCols_raw, day_override=day_override)
    
    CasesVisualise(dataDir, measureCols, dayStartOffset=dayStartOffset)
    InfectionsAndStageVisualise(dataDir, measureCols, dayStartOffset=dayStartOffset)
    
    
    