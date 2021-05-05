import math
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import os
import re

from utilities import OutputToFile, GetCohortData


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
    fileList = [x for x in fileList if '_head' not in x]
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


############### Infection Step 1 ###############

def SetAgeRange(x):
    if x < 18:
        return 0
    elif x < 35:
        return 18
    elif x < 65:
        return 35
    else:
        return 65


def ProcessInfectChunk(df, chortDf, outputPrefix, months):
    df.columns.set_levels(df.columns.levels[1].astype(int), level=1, inplace=True)
    df.columns.set_levels(df.columns.levels[2].astype(int), level=2, inplace=True)
    df.sort_values(['cohort', 'day'], axis=1, inplace=True)
    
    col_index = df.columns.to_frame()
    col_index.reset_index(drop=True, inplace=True)
    col_index['year'] = np.floor(col_index['day']/365).astype(int)
    col_index = pd.merge(col_index, chortDf,
                         on='cohort',
                         how='left',
                         sort=False)
    col_index = col_index.drop(columns=['atsi', 'morbid'])
    col_index['age_min'] = col_index['age'].apply(SetAgeRange)
    df.columns = pd.MultiIndex.from_frame(col_index)
    
    df = df.groupby(level=[5, 3], axis=1).sum()
    
    OutputToFile(df, outputPrefix)


def ProcessInfectCohorts(measureCols, filename, cohortFile, outputPrefix, months):
    cohortData = GetCohortData(cohortFile)
    chunksize = 4 ** 7
    
    for chunk in tqdm(pd.read_csv(filename + '.csv', 
                             index_col=list(range(4 + len(measureCols))),
                             header=list(range(3)),
                             dtype={'day' : int, 'cohort' : int},
                             chunksize=chunksize),
                      total=4):
        ProcessInfectChunk(chunk, cohortData, outputPrefix, months)
         
############### Sum vaccine and non-vaccine infections ###############

def GetInfectionTable(measureCols, path, filename):
    df = pd.read_csv(path + filename + '.csv', 
                             index_col=list(range(4 + len(measureCols))),
                             header=list(range(2)))
    index = df.index.to_frame()
    index = index.drop(columns=['run', 'global_transmissibility'])
    df.index = pd.MultiIndex.from_frame(index)
    return df
    

def AddAndCleanInfections(subfolder, measureCols):
    df_infect_vac = GetInfectionTable(measureCols, subfolder + '/Report_process/', 'infect_vac')
    df_infect_NoVac = GetInfectionTable(measureCols, subfolder + '/Report_process/', 'infect_noVac')
    OutputToFile(df_infect_vac + df_infect_NoVac, subfolder + '/Report_process/infect_total')

############### Stage Step 1 ###############
 
def ProcessChunkStage(df, outputPrefix):
    df.columns.set_levels(df.columns.levels[1].astype(int), level=1, inplace=True)
    df.columns.set_levels(df.columns.levels[2].astype(int), level=2, inplace=True)
    
    df.columns = df.columns.droplevel([0, 2])
    
    col_index = df.columns.to_frame()
    col_index.reset_index(drop=True, inplace=True)
    col_index['year'] = np.floor(col_index['day']/365).astype(int)
    df.columns = pd.MultiIndex.from_frame(col_index)
    
    df = df.apply(lambda c: [1 if x > 2 else 0 for x in c])
    df = df.groupby(level=[1], axis=1).mean()
    
    index = df.index.to_frame()
    index = index.drop(columns=['run', 'global_transmissibility'])
    df.index = pd.MultiIndex.from_frame(index)
    
    OutputToFile(df, outputPrefix)


def ProcessStageCohorts(measureCols, filename, outputPrefix):
    chunksize = 4 ** 7
    
    for chunk in tqdm(pd.read_csv(filename + '.csv', 
                             index_col=list(range(4 + len(measureCols))),
                             header=list(range(3)),
                             dtype={'day' : int, 'cohort' : int},
                             chunksize=chunksize),
                      total=4):
        ProcessChunkStage(chunk, outputPrefix)


############### Median Table Shared ###############

def SmartFormat(x):
    if x > 1:
        return '{:,.0f}'.format(x)
    return '{:,.2f}%'.format(x*100)

def ShapeMedianTable(df, measure, toSort):
    df = df.transpose()[measure]
    df = df.unstack('RolloutMonths')
    df = df.reset_index().set_index(toSort).sort_index()
    return df


def OutputMedianUncertainTables(df, outFile, toSort):
    df = df.describe(percentiles=[0.1, 0.9])
    df_med = ShapeMedianTable(df, '50%', toSort).applymap(SmartFormat)
    df_upper = ShapeMedianTable(df, '90%', toSort).applymap(SmartFormat)
    df_lower = ShapeMedianTable(df, '10%', toSort).applymap(SmartFormat)
    df_out = df_med + ' (' + df_lower + ' to ' + df_upper + ')'
    OutputToFile(df_out, outFile)
    

def ConstructMedian(df, measure, outFile):
    df = df.unstack('RolloutMonths')
    OutputMedianUncertainTables(df, outFile, measure)
    

def ConstructGroupedMedian(df, measure, outFile):
    df = df.unstack('rand_seed').stack(measure)
    df = df.transpose().describe().transpose()['mean']
    df = df.unstack(['RolloutMonths'] + measure)
    OutputMedianUncertainTables(df, outFile, measure)
    

def ConstructGroupedMedianNoVacCompare(df, measure, outFile):
    df = df.unstack('rand_seed').stack(measure)
    df = df.transpose().describe().transpose()['mean']
    df = df.unstack(['RolloutMonths'] + measure)
    df = df.sub(df[0], axis=0) * -1
    OutputMedianUncertainTables(df, outFile, measure)
    

############### Median Table Processing ###############

def OutputInfectReportTables(subfolder, measureCols):
    infectFile = subfolder + '/Report_process/infect_total'
    infectDf = pd.read_csv(infectFile + '.csv', 
                             index_col=list(range(2 + len(measureCols))),
                             header=list(range(2)))
    
    measure = ['year', 'age_min']
    print('ConstructMedian Infect')
    ConstructMedian(infectDf, measure, subfolder + '/Report_out/bigMedian')
    print('ConstructGroupedMedian Infect')
    ConstructGroupedMedian(infectDf, measure, subfolder + '/Report_out/groupedMedian')
    print('ConstructGroupedMedianNoVacCompare Infect')
    ConstructGroupedMedianNoVacCompare(infectDf, measure, subfolder + '/Report_out/groupedMinusNoVac')

    
def OutputStageReportTables(subfolder, measureCols):
    stageFile = subfolder + '/Report_process/stage'
    stageDf = pd.read_csv(stageFile + '.csv', 
                             index_col=list(range(2 + len(measureCols))),
                             header=[0])
    col_index = stageDf.columns.to_frame().rename(columns={0 : 'year'})
    stageDf.columns = pd.MultiIndex.from_frame(col_index)
    measure = ['year']
    
    print('ConstructMedian Stage')
    ConstructMedian(stageDf, measure, subfolder + '/Report_out/bigMedian_stage')
    print('ConstructGroupedMedian Stage')
    ConstructGroupedMedian(stageDf, measure, subfolder + '/Report_out/groupedMedian_stage')
    print('ConstructGroupedMedianNoVacCompare Stage')
    ConstructGroupedMedianNoVacCompare(stageDf, measure, subfolder + '/Report_out/groupedMinusNoVac_stage')
    
############### Median Table Processing ###############


def GroupedMedianByVaccinationSpeed_sum(df, measure):
    df = df.unstack('rand_seed').stack(measure)
    df = df.transpose().describe().transpose()['mean']
    df = df.unstack(['RolloutMonths'] + measure)
    df = df.groupby(level=[0], axis=1).sum()
    return df

def GroupedMedianByVaccinationSpeed_mean(df, measure):
    df = df.unstack('rand_seed').stack(measure)
    df = df.transpose().describe().transpose()['mean']
    df = df.unstack(['RolloutMonths'] + measure)
    df = df.groupby(level=[0], axis=1).mean()
    return df


def SplitDfByMeasure(df, measure=False):
    if measure:
        df = df.unstack(measure)
        
    df = df.describe(percentiles=[0.1, 0.9])
    df = df.transpose()
    if measure:
        df = df.unstack(measure)
    #print(df[['50%']].applymap(SmartFormat))
    
    df_med = df[['50%']].applymap(SmartFormat)
    df_upper = df[['90%']].applymap(SmartFormat)
    df_lower = df[['10%']].applymap(SmartFormat)
    
    if measure:
        df_med.columns = df_med.columns.droplevel(0)
        df_upper.columns = df_upper.columns.droplevel(0)
        df_lower.columns = df_lower.columns.droplevel(0)
    else:
        df_med = df_med.rename(columns={'50%' : 'value'})
        df_upper = df_upper.rename(columns={'90%' : 'value'})
        df_lower = df_lower.rename(columns={'10%' : 'value'})
    
    df_out = df_med + ' (' + df_lower + ' to ' + df_upper + ')'
    return df_out


def OutputLineCompare(infectDf, stageDf, measure=False, paramList=False, path=''):
    if measure:
        print('Output ' + measure)
    else:
        print('Output Full')
    infectDf = SplitDfByMeasure(infectDf, measure)
    stageDf = SplitDfByMeasure(stageDf, measure)
    print(infectDf)
    print(stageDf)
    if paramList:
        for param in paramList:
            OutputToFile(infectDf[[param]].transpose().reset_index(drop=True), path)
            OutputToFile(stageDf[[param]].transpose().reset_index(drop=True), path)
    else:
        OutputToFile(infectDf.transpose().reset_index(drop=True), path)
        OutputToFile(stageDf.transpose().reset_index(drop=True), path)


def MakeTableFive(subfolder, measureCols):
    print('MakeTableFive load stage file')
    stageFile = subfolder + '/Report_process/stage'
    sDf = pd.read_csv(stageFile + '.csv', 
                             index_col=list(range(2 + len(measureCols))),
                             header=[0])
    col_index = sDf.columns.to_frame().rename(columns={0 : 'year'})
    sDf.columns = pd.MultiIndex.from_frame(col_index)
    
    print('MakeTableFive load infect file')
    infectFile = subfolder + '/Report_process/infect_total'
    iDf = pd.read_csv(infectFile + '.csv', 
                             index_col=list(range(2 + len(measureCols))),
                             header=list(range(2)))

    print('MakeTableFive group stage file')
    sDf = GroupedMedianByVaccinationSpeed_mean(sDf, ['year'])
    print('MakeTableFive group infect file')
    iDf = GroupedMedianByVaccinationSpeed_sum(iDf, ['year', 'age_min'])
    
    path = subfolder + '/Report_out/table5'
    OutputLineCompare(iDf, sDf, False, False, path)
    OutputLineCompare(iDf, sDf, 'R0', [2.5, 3], path)
    OutputLineCompare(iDf, sDf, 'param_policy', ['ModerateSupress', 'ModerateSupress_No_4'], path)
    OutputLineCompare(iDf, sDf, 'VacEfficacy', [0.95, 0.875, 0.75], path)
    OutputLineCompare(iDf, sDf, 'Var_R0_mult', [1.3, 1.45, 1.6], path)
    OutputLineCompare(iDf, sDf, 'VacEff_VarMult', [0.95, 0.8], path)
    OutputLineCompare(iDf, sDf, 'VacKids', ['No', 'Yes'], path)
    
    
############### Organisation (mostly for commenting) ###############

def ProcessInfectionCohorts(subfolder, measureCols, months):
    print('Processing vaccination infection for PMSLT')
    ProcessInfectCohorts(measureCols,
                         subfolder + '/ABM_process/processed_infectVac',
                         subfolder + '/ABM_process/processed_static',
                         subfolder + '/Report_process/infect_vac',
                         months)
    print('Processing non-vaccination infection for PMSLT')
    ProcessInfectCohorts(measureCols,
                         subfolder + '/ABM_process/processed_infectNoVac',
                         subfolder + '/ABM_process/processed_static',
                         subfolder + '/Report_process/infect_noVac',
                         months)

def ProcessStages(subfolder, measureCols):
    ProcessStageCohorts(measureCols,
                        subfolder + '/ABM_process/processed_stage',
                        subfolder + '/Report_process/stage')


def ProcessInfection(subfolder, measureCols, months=12):
    ProcessInfectionCohorts(subfolder, measureCols, months)

###############  ###############

def DoProcessingForReport(subfolder, measureCols, months=12):
    #ProcessStages(subfolder, measureCols)
    #ProcessInfection(subfolder, measureCols, months)
    #AddAndCleanInfections(subfolder, measureCols)
    
    #OutputInfectReportTables(subfolder, measureCols)
    #OutputStageReportTables(subfolder, measureCols)
    
    MakeTableFive(subfolder, measureCols)
