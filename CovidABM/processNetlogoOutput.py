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


def ProcessAbmChunk(chunk: pd.DataFrame, outputStaticData, filename):
    # Drop colums that are probably never useful.
    
    chunk = chunk[[
        '[run number]', 'rand_seed', 'param_policy', 'global_transmissibility',
        'param_vac1_tran_reduct', 'param_vac2_tran_reduct', 'param_vac_uptake',
        'param_trigger_loosen',
        'stage_listOut', 'scalephase', 'cumulativeInfected', 'casesReportedToday',
        'Deathcount', 'totalOverseasIncursions', 'infectNoVacArray_listOut', 'infectVacArray_listOut',
        'age_listOut', 'atsi_listOut', 'morbid_listOut',
    ]]
    
    cohorts = len(chunk.iloc[0].age_listOut.split(' '))
    days = len(chunk.iloc[0].stage_listOut.split(' '))
    
    if outputStaticData:
        staticData = pd.DataFrame(chunk[['age_listOut', 'atsi_listOut', 'morbid_listOut']].transpose()[0])
        staticData = SplitNetlogoList(staticData, cohorts, 0, '').transpose()
        staticData = staticData.rename(columns={'age_listOut': 'age', 'atsi_listOut': 'atsi', 'morbid_listOut': 'morbid'})
        OutputToFile(staticData, filename + '_static') 
    
    chunk = chunk.drop(['age_listOut', 'atsi_listOut', 'morbid_listOut'], axis=1)
    chunk = chunk.rename(mapper={'[run number]' : 'run'}, axis=1)
    chunk = chunk.set_index([
        'run', 'rand_seed', 'param_policy', 'global_transmissibility',
        'param_vac1_tran_reduct', 'param_vac2_tran_reduct',
        'param_vac_uptake', 'param_trigger_loosen',
    ])
    
    secondaryData = [
        'scalephase', 'cumulativeInfected', 'casesReportedToday',
        'Deathcount', 'totalOverseasIncursions'
    ]
    
    OutputToFile(chunk[secondaryData], filename + '_secondary')
    chunk = chunk.drop(secondaryData, axis=1)
    
    index = chunk.index.to_frame()
    index['R0'] = index['global_transmissibility'].replace({
        0.34 : 2.5,
        0.43 : 3.125,
        0.54 : 3.75,})
    chunk.index = pd.MultiIndex.from_frame(index)
    
    SplitOutDailyData(chunk, 1, days, 'stage', filename, 'stage')
    SplitOutDailyData(chunk, cohorts, days, 'infectNoVacArray', filename, 'infectNoVac')
    SplitOutDailyData(chunk, cohorts, days, 'infectVacArray', filename, 'infectVac')


def ProcessAbmOutput(outputFile, filelist):
    chunksize = 4 ** 7
    
    firstProcess = True
    for filename in filelist:
        size = os.path.getsize(filename + '.csv')
        for chunk in tqdm(pd.read_csv(filename + '.csv', chunksize=chunksize, header=6), total=4):
            ProcessAbmChunk(chunk, firstProcess, outputFile)
            firstProcess = False


def ToVisualisation(chunk, filename, append):
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


def ProcessFileToVisualisation(filename, append):
    chunksize = 4 ** 7
    for chunk in tqdm(pd.read_csv(filename + '_' + append + '.csv', chunksize=chunksize,
                                  index_col=list(range(9)),
                                  header=list(range(3)),
                                  dtype={'day' : int, 'cohort' : int}),
                      total=4):
        ToVisualisation(chunk, filename, append)


def MakeInfectionHeatmap(outputFile, inputFile, startWeek=13, window=26):
    df = pd.read_csv(inputFile + '.csv', index_col=list(range(9)),
                                  header=list(range(1)))
    df = df.groupby(level=[2, 3, 4, 5, 6, 7, 8], axis=0).mean()
    # Do (startWeek + 1) because week 0 consists of a single day, day 0.
    df = df[[str(i + startWeek + 1) + '.0' for i in range(window)]]
    df = df.transpose().describe().transpose()
    df = df[['mean']]
    
    df = df.reset_index()
    df = df[df['param_vac1_tran_reduct'] == df['param_vac2_tran_reduct']]
    df = df.drop(columns=['param_vac2_tran_reduct', 'global_transmissibility'])
    df = df.rename(columns={'param_vac1_tran_reduct' : 'param_vac_tran_reduct'})

    df = ToHeatmap(df,
        ['R0', 'param_trigger_loosen', 'param_vac_uptake'],
        ['param_policy', 'param_vac_tran_reduct'],
        sort_rows=[
            ['R0', {
                2.5 : 'a',
                3.125 : 'b',
                3.75 : 'c',
            }],
            ['param_trigger_loosen', {
                False : 'a',
                True : 'b',
            }],
            ['param_vac_uptake', {
                90 : 'a',
                75 : 'b',
                60 : 'c',
            }],
        ], 
        sort_cols=[
            ['param_policy', {
                'AggressElim' : 'a',
                'ModerateElim' : 'b',
                'TightSupress' : 'c',
                'LooseSupress' : 'd'
            }],
            ['param_vac_tran_reduct', {
                90 : 'a',
                75 : 'b',
                50 : 'c',
            }],
        ]
    )
    OutputToFile(df, outputFile)
    

def MakeStagesHeatmap(outputFile, inputFile, startWeek=13, window=26):
    df = pd.read_csv(inputFile + '.csv', index_col=list(range(9)),
                                  header=list(range(3)))
    df = df.apply(lambda c: [1 if x > 2 else 0 for x in c])
    df = df.groupby(level=[2, 3, 4, 5, 6, 7, 8], axis=0).mean()
    
    df = df.droplevel([0, 2], axis=1)
    # Add 1 to the day because week 0 consists of a single day, day 0.
    df = df[[str(i + startWeek*7 + 1) for i in range(window*7)]]
    df = df.transpose().describe().transpose()
    df = df[['mean']]
    
    df = df.reset_index()
    df = df[df['param_vac1_tran_reduct'] == df['param_vac2_tran_reduct']]
    df = df.drop(columns=['param_vac2_tran_reduct', 'global_transmissibility'])
    df = df.rename(columns={'param_vac1_tran_reduct' : 'param_vac_tran_reduct'})
    
    df = ToHeatmap(df,
        ['R0', 'param_trigger_loosen', 'param_vac_uptake'],
        ['param_policy', 'param_vac_tran_reduct'],
        sort_rows=[
            ['R0', {
                2.5 : 'a',
                3.125 : 'b',
                3.75 : 'c',
            }],
            ['param_trigger_loosen', {
                False : 'a',
                True : 'b',
            }],
            ['param_vac_uptake', {
                90 : 'a',
                75 : 'b',
                60 : 'c',
            }],
        ], 
        sort_cols=[
            ['param_policy', {
                'AggressElim' : 'a',
                'ModerateElim' : 'b',
                'TightSupress' : 'c',
                'LooseSupress' : 'd'
            }],
            ['param_vac_tran_reduct', {
                90 : 'a',
                75 : 'b',
                50 : 'c',
            }],
        ]
    )
    OutputToFile(df, outputFile)


def DoAbmProcessing(subfolder):
    abmDir = subfolder + '/ABM_out/'
    processDir = subfolder + '/ABM_process/'
    
    print('Processing ABM Output', subfolder)
    ProcessAbmOutput(processDir + 'processed', [abmDir + 'mergedresult'])
    
    print('Processing infectNoVac')
    ProcessFileToVisualisation(processDir + 'processed', 'infectNoVac') 
    print('Processing infectVac')
    ProcessFileToVisualisation(processDir + 'processed', 'infectVac')
    AddFiles(processDir + 'infect_unique_weeklyAgg',
        [
            processDir + 'processed_infectNoVac_weeklyAgg',
            processDir + 'processed_infectVac_weeklyAgg',
        ],
        index=9
    )


def MakeHeatmaps(subfolder):
    processDir = subfolder + '/ABM_process/'
    visualDir = subfolder + '/ABM_heatmaps/'
    
    print('Processing MakeInfectionHeatmap stage 2')
    MakeInfectionHeatmap(visualDir + 'infect_average_weekly_stage2',
                         processDir + 'infect_unique_weeklyAgg',
                         startWeek=13, window=26)
    print('Processing MakeStagesHeatmap stage 2')
    MakeStagesHeatmap(visualDir + 'lockdown_proportion_stage2',
                      processDir + 'processed_stage',
                      startWeek=13, window=26)
    
    print('Processing MakeInfectionHeatmap stage 2b')
    MakeInfectionHeatmap(visualDir + 'infect_average_weekly_stage2b_only',
                         processDir + 'infect_unique_weeklyAgg',
                         startWeek=26, window=13)
    print('Processing MakeStagesHeatmap stage 2b')
    MakeStagesHeatmap(visualDir + 'lockdown_proportion_stage2b_only',
                      processDir + 'processed_stage',
                      startWeek=26, window=13)
