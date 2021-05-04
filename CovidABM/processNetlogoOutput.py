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


def ProcessAbmChunk(chunk: pd.DataFrame, outputStaticData, filename, measureCols_raw, day_override=False):
    # Drop colums that are probably never useful.
    
    chunk = chunk[[
        '[run number]', 'rand_seed',
        'stage_listOut', 'scalephase', 'cumulativeInfected', 'casesReportedToday',
        'Deathcount', 'totalOverseasIncursions', 'infectNoVacArray_listOut', 'infectVacArray_listOut',
        'age_listOut', 'atsi_listOut', 'morbid_listOut',
        'global_transmissibility'
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
    chunk = chunk.set_index([
        'run', 'rand_seed', 'param_policy', 'global_transmissibility',
    ] + measureCols_raw)
    
    secondaryData = [
        'scalephase', 'cumulativeInfected', 'casesReportedToday',
        'Deathcount', 'totalOverseasIncursions'
    ]
    
    OutputToFile(chunk[secondaryData], filename + '_secondary')
    chunk = chunk.drop(secondaryData, axis=1)
    
    index = chunk.index.to_frame()
    index['R0'] = index['global_transmissibility'].apply(lambda x: 2.5 if x < 0.3 else 3)
    index['param_final_phase'] = index['param_final_phase'].replace({
        -1 : 'Yes',
        5 : 'No',
    })
    index['param_vac_rate_mult'] = index['param_vac_rate_mult'].replace({
        0.75 : 16,
        1 : 12,
        1.5 : 8
    })
    index = index.rename(columns={
        'param_final_phase' : 'VacKids',
        'param_vac_rate_mult' : 'RolloutMonths',
        'vac_variant_eff_prop' : 'VacEff_VarMult',
        'variant_transmiss_growth' : 'Var_R0_mult',
        'param_vac_tran_reduct' : 'VacEfficacy',
    })
    
    chunk.index = pd.MultiIndex.from_frame(index)
    
    SplitOutDailyData(chunk, 1, days, 'stage', filename, 'stage')
    SplitOutDailyData(chunk, cohorts, days, 'infectNoVacArray', filename, 'infectNoVac')
    SplitOutDailyData(chunk, cohorts, days, 'infectVacArray', filename, 'infectVac')


def ProcessAbmOutput(subfolder, measureCols_raw, day_override=False):
    outputFile = subfolder + '/ABM_process/' + 'processed'
    filelist = [subfolder + '/ABM_out/' + 'MergedResults']
    chunksize = 4 ** 7
    
    firstProcess = True
    for filename in filelist:
        for chunk in tqdm(pd.read_csv(filename + '.csv', chunksize=chunksize, header=6), total=4):
            ProcessAbmChunk(chunk, firstProcess, outputFile, measureCols_raw, day_override=day_override)
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
                                  index_col=list(range(4 + len(measureCols))),
                                  header=list(range(3)),
                                  dtype={'day' : int, 'cohort' : int}),
                      total=4):
        ToVisualisation(chunk, filename, append, measureCols)

def HeatmapProcess(df):
    df = df.reset_index()
    df = df.drop(columns=['global_transmissibility'])

    df = ToHeatmap(df,
        ['param_policy', 'Var_R0_mult', 'R0', 'VacKids'],
        ['VacEfficacy', 'VacEff_VarMult', 'RolloutMonths'],
        sort_rows=[
            ['param_policy', {
                'ModerateSupress_No_4' : 'b',
                'ModerateSupress' : 'a',
            }],
            ['Var_R0_mult', {
                1.3 : 'a',
                1.45 : 'b',
                1.6 : 'c',
            }],
            ['R0', {
                2.5 : 'a',
                3 : 'b',
            }],
            ['VacKids', {
                'Yes' : 'a',
                'No' : 'b',
            }],
        ], 
        sort_cols=[
            ['VacEfficacy', {
                0.75 : 'c',
                0.875 : 'b',
                0.95 : 'a',
            }],
            ['VacEff_VarMult', {
                0.8 : 'b',
                0.95 : 'a',
            }],
            ['RolloutMonths', {
                8 : 'a',
                12 : 'b',
                16 : 'c',
            }],
        ]
    )
    return df
    

def MakeInfectionHeatmap(name, outputFile, inputFile, measureCols, startWeek=13, window=26):
    
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(4 + len(measureCols))),
                     header=list(range(1)))
    df = df.groupby(level=list(range(2, 4 + len(measureCols))), axis=0).mean()
    # Do (startWeek + 1) because week 0 consists of a single day, day 0.
    df = df[[str(i + startWeek + 1) + '.0' for i in range(window)]]
    df = df.transpose().describe().transpose()
    df = df[['50%']] / 7
    df = df.rename(columns={'50%' : name})
    
    df = HeatmapProcess(df)
    OutputToFile(df, outputFile)
    

def MakeStagesHeatmap(name, outputFile, inputFile, measureCols, startWeek=13, window=26):
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(4 + len(measureCols))),
                     header=list(range(3)))
    df = df.apply(lambda c: [1 if x > 2 else 0 for x in c])
    df = df.groupby(level=list(range(2, 4 + len(measureCols))), axis=0).mean()
    
    df = df.droplevel([0, 2], axis=1)
    # Add 1 to the day because week 0 consists of a single day, day 0.
    df = df[[str(i + startWeek*7 + 1) for i in range(window*7)]]
    df = df.transpose().describe().transpose()
    df = df[['50%']]
    df = df.rename(columns={'50%' : name})
    
    df = HeatmapProcess(df)
    OutputToFile(df, outputFile)

    
def DoAbmProcessing(dataDir, measureCols, measureCols_raw, day_override=False):
    print('Processing ABM Output', dataDir)
    ProcessAbmOutput(dataDir, measureCols_raw, day_override=day_override)
    
    print('Processing infectNoVac')
    ProcessFileToVisualisation(dataDir, 'infectNoVac', measureCols) 
    print('Processing infectVac')
    ProcessFileToVisualisation(dataDir, 'infectVac', measureCols)
    AddFiles(dataDir + '/ABM_process/' + 'infect_unique_weeklyAgg',
        [
            dataDir + '/ABM_process/' + 'processed_infectNoVac_weeklyAgg',
            dataDir + '/ABM_process/' + 'processed_infectVac_weeklyAgg',
        ],
        index=(4 + len(measureCols))
    )


def MakeHeatmaps(dataDir, measureCols):
    processDir = dataDir + '/ABM_process/'
    visualDir = dataDir + '/ABM_heatmaps/'
    
    print('Processing MakeInfectionHeatmap full')
    MakeInfectionHeatmap('full',
                         visualDir + 'infect_average_daily_full',
                         processDir + 'infect_unique_weeklyAgg',
                         measureCols,
                         startWeek=0, window=104)
    print('Processing MakeStagesHeatmap stage full')
    MakeStagesHeatmap('full',
                      visualDir + 'lockdown_proportion_full',
                      processDir + 'processed_stage',
                      measureCols,
                      startWeek=0, window=104)
    
    start = 0
    for i in range(4):
        print('Processing ' + str(start) + '_to_' + str(start + 26))
        MakeInfectionHeatmap(str(start) + '_to_' + str(start + 26),
                             visualDir + 'infect_average_daily_' + str(start) + '_to_' + str(start + 26),
                             processDir + 'infect_unique_weeklyAgg',
                             measureCols,
                             startWeek=start, window=26)
        MakeStagesHeatmap(str(start) + '_to_' + str(start + 26),
                          visualDir + 'lockdown_proportion_' + str(start) + '_to_' + str(start + 26),
                          processDir + 'processed_stage',
                          measureCols,
                          startWeek=start, window=26)
        start = start + 26


dataDir = '2021_04_29'
measureCols =  ['param_policy', 'param_vac_rate_mult', 'param_final_phase',
        'variant_transmiss_growth', 'param_vac_tran_reduct', 'vac_variant_eff_prop']
