
import math
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import os
import re

from utilities import OutputToFile

############### Shared ###############

def Output(df, path):
    index = df.index.to_frame(index=False)
    index = index.drop(columns=['run', 'global_transmissibility'])
    df.index = pd.MultiIndex.from_frame(index)
    df = df.rename('value')
    
    # Consider the following as a nicer replacement:
    #"for name, subDf in df.groupby(level=0):"
    for value in index.rand_seed.unique():
        rdf = df[df.index.isin([value], level=0)]
        rdf = rdf.reset_index()
        rdf = rdf.drop(columns='rand_seed')
        OutputToFile(rdf, path + '_' + str(value), index=False)


def LoadColumn(path, inName, indexCols):
    return pd.read_csv(path + '_' + inName + '.csv',
                header=[0],
                index_col=list(range(indexCols)))


def CombineDrawColumnsAndFindDraw0(prefix, append, index_size=8):
    fileList = os.listdir(prefix)
    nameList = list(set(list(map(
        lambda x: int(x[re.search(r'\d', x).start():x.find('.')]), fileList))))
    nameList.sort()
    
    draw_prefix = prefix + append
    df = None
    for n, value in tqdm(enumerate(nameList), total=len(nameList)):
        if n == 0:
            df = LoadColumn(draw_prefix, str(value), index_size)
            df.rename(columns={'value' : 'draw_1'}, inplace=True)
        else:
            df['draw_' + str(n + 1)] = LoadColumn(draw_prefix, str(value), index_size)['value']

    df['draw_0'] = df.mean(axis=1)
    return df    


############### Infection Step 1 - Make two csvs for each random seed ###############

def GetCohortData(cohortFile):
    df = pd.read_csv(cohortFile + '.csv', 
                index_col=[0],
                header=[0])
    df.index.rename('cohort', True)
    df = df.reset_index()
    df['cohort'] = df['cohort'].astype(int)
    df['age'] = df['age'].astype(int)
    return df


def ProcessInfectChunk(df, chortDf, outputPrefix):
    df.columns.set_levels(df.columns.levels[1].astype(int), level=1, inplace=True)
    df.columns.set_levels(df.columns.levels[2].astype(int), level=2, inplace=True)
    df.sort_values(['cohort', 'day'], axis=1, inplace=True)
    
    col_index = df.columns.to_frame()
    col_index.reset_index(drop=True, inplace=True)
    col_index['month'] = np.floor(col_index['day']*12/365).astype(int)
    col_index = pd.merge(col_index, chortDf,
                         on='cohort',
                         how='left',
                         sort=False)
    col_index = col_index.drop(columns=['atsi', 'morbid'])
    df.columns = pd.MultiIndex.from_frame(col_index)
    
    df = df.groupby(level=[4, 3], axis=1).sum()
    
    # In the ABM age range 15 represents ages 10-17 while age range 25 is
    # ages 18-30. First redestribute these cohorts sothey align with 10 year
    # increments.
    df[15], df[25] = df[15] + df[25]/5, df[25]*4/5

    
    # Then split the 10 year cohorts in half.
    ageCols = [i*10 + 5 for i in range(10)]
    for age in ageCols:
        for j in range(12):
            # TODO, vectorise?
            df[age - 2.5, j] = df[age, j]/2
            df[age + 2.5, j] = df[age, j]/2
    
    # Add extra cohorts missing from ABM
    # Very few people are over 100
    for j in range(12):
        df[102.5, j] = 0
        df[107.5, j] = 0
    
    df = df.drop(columns=ageCols, level=0)
    df = df.stack(level=[0,1])
    Output(df, outputPrefix)
    

def ProcessInfectCohorts(filename, cohortFile, outputPrefix):
    cohortData = GetCohortData(cohortFile)
    chunksize = 4 ** 7
    
    for chunk in tqdm(pd.read_csv(filename + '.csv', 
                             index_col=list(range(9)),
                             header=list(range(3)),
                             dtype={'day' : int, 'cohort' : int},
                             chunksize=chunksize),
                      total=4):
        ProcessInfectChunk(chunk, cohortData, outputPrefix)


############### Infection Step 2 ###############


def GetEffectsData(file):
    df = pd.read_csv(file + '.csv',
                header=[0])
    df = df.set_index(['vaccine', 'age_start', 'sex'])
    return df


def ProcessInfectionTable(df):
    index = df.index.to_frame()
    index['year_start'] = (index['month'])/12
    index['year_end']   = (index['month'] + 1)/12
    index['age_start']  = index['age'] - 2.5
    index['age_end']    = index['age'] + 2.5
    index = index.drop(columns=['age', 'month'])
    df.index = pd.MultiIndex.from_frame(index)
    
    enddf = df[df.index.isin([11.5/12], level=7)]
    enddf = enddf*0
    index = enddf.index.to_frame()
    index['year_start'] = index['year_end']
    index['year_end']   = 120
    enddf.index = pd.MultiIndex.from_frame(index)
    df = df.append(enddf)
    
    df = pd.concat([df, df], axis=1, keys=('male','female'))/2
    df.columns.set_names('sex', level=[0], inplace=True)
    df = df.stack(level=[0])
    
    df.index = df.index.reorder_levels(order=[
        'param_policy', 'param_vac_uptake', 'param_vac1_tran_reduct',
        'param_vac2_tran_reduct', 'param_trigger_loosen', 'R0', 'sex',
        'age_start', 'age_end', 'year_start', 'year_end'])
    
    return df


def MultiplyByCohortEffect(df, multDf):
    df = df.mul(multDf, axis=0)
    return df
    

def AddInfectionMortMorbAndFinalise(subfolder, path, output):
    cohortEffect = GetEffectsData(subfolder + '/other_input/chort_effects')
    
    df_infect_vac = CombineDrawColumnsAndFindDraw0(path + 'infect_results/', 'infect_vac', index_size=8)
    df_infect_vac = ProcessInfectionTable(df_infect_vac)
    
    df_infect_NoVac = CombineDrawColumnsAndFindDraw0(path + 'infect_results/', 'infect_noVac', index_size=8)
    df_infect_NoVac = ProcessInfectionTable(df_infect_NoVac)
    
    df_mort_vac   = MultiplyByCohortEffect(df_infect_vac, cohortEffect.loc[1]['mort'])
    df_mort_noVac = MultiplyByCohortEffect(df_infect_NoVac, cohortEffect.loc[0]['mort'])
    df_morb_vac   = MultiplyByCohortEffect(df_infect_vac, cohortEffect.loc[1]['morb'])
    df_morb_noVac = MultiplyByCohortEffect(df_infect_NoVac, cohortEffect.loc[0]['morb'])
    
    OutputToFile(df_mort_vac + df_mort_noVac, output + '/acute_disease.covid.mortality')
    OutputToFile(df_morb_vac + df_morb_noVac, output + '/acute_disease.covid.morbidity')


############### Stages Step 1 - Output each random seed to csv ###############     

def ProcessChunkStage(df, outputPrefix):
    df.columns.set_levels(df.columns.levels[1].astype(int), level=1, inplace=True)
    df.columns.set_levels(df.columns.levels[2].astype(int), level=2, inplace=True)
    
    df.columns = df.columns.droplevel([0, 2])
    
    col_index = df.columns.to_frame()
    col_index.reset_index(drop=True, inplace=True)
    col_index['month'] = np.floor(col_index['day']*12/365).astype(int)
    df.columns = pd.MultiIndex.from_frame(col_index)
    
    df = df.apply(lambda c: [1 if x > 2 else 0 for x in c])
    df = df.groupby(level=[1], axis=1).mean()
    
    df = df.stack(level=[0])
    Output(df, outputPrefix)


def ProcessStageCohorts(filename, outputPrefix):
    chunksize = 4 ** 7
    
    for chunk in tqdm(pd.read_csv(filename + '.csv', 
                             index_col=list(range(9)),
                             header=list(range(3)),
                             dtype={'day' : int, 'cohort' : int},
                             chunksize=chunksize),
                      total=4):
        ProcessChunkStage(chunk, outputPrefix)


############### Stages Step 2 - Combine and Process ###############

def CombineDrawsStageAndFinalise(subfolder, path, output):
    df = CombineDrawColumnsAndFindDraw0(path, 'stage', index_size=7)
    
    index = df.index.to_frame()
    index = index[['param_policy', 'param_vac_uptake', 'param_vac1_tran_reduct',
                   'param_vac2_tran_reduct', 'param_trigger_loosen', 'R0', 'month']]
    index['year_start'] = (index['month'])/12
    index['year_end']   = (index['month'] + 1)/12
    index['R0'] = index['R0'].replace({0.43 : 3.125,})
    index = index.drop(columns=['month'])
    df.index = pd.MultiIndex.from_frame(index)

    enddf = df[df.index.isin([11.5/12], level=7)]
    enddf = enddf*0
    index = enddf.index.to_frame()
    index['year_start'] = index['year_end']
    index['year_end']   = 120
    enddf.index = pd.MultiIndex.from_frame(index)
    df = df.append(enddf)
    
    OutputToFile(df, output + '/lockdown_stage')


############### Run Infection Processing ###############

def DoProcessingForPMSLT(subfolder):
    print('Processing vaccination infection for PMSLT')
    ProcessInfectCohorts(subfolder + '/ABM_process/processed_infectVac',
                         subfolder + '/ABM_process/processed_static',
                         subfolder + '/PMSLT_process/infect_results/infect_vac')
    print('Processing non-vaccination infection for PMSLT')
    ProcessInfectCohorts(subfolder + '/ABM_process/processed_infectNoVac',
                         subfolder + '/ABM_process/processed_static',
                         subfolder + '/PMSLT_process/infect_results/infect_noVac')
    
    print('Finalising infection PMSLT input')
    AddInfectionMortMorbAndFinalise(subfolder, subfolder + '/PMSLT_process/', subfolder + '/PMSLT_input')

    print('Processing stages for PMSLT')
    ProcessStageCohorts(subfolder + '/ABM_process/processed_stage', subfolder + '/PMSLT_process/stage_results/stage')
    print('Finalising stages PMSLT input')
    CombineDrawsStageAndFinalise(subfolder, subfolder + '/PMSLT_process/stage_results/', subfolder + '/PMSLT_input')