# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 12:16:11 2021

@author: wilsonte
"""
import pandas as pd
import numpy as np

from utilities import AddFiles
from utilities import ToHeatmap, CrossIndex
from utilities import OutputToFile, GetCohortData, ListRemove

measureCols_global =  ['r0_range', 'policy_pipeline', 'VacKids', 'param_vacincurmult', 'param_vac_uptake'] 

dataDir = 'Vic2/2021_07_05'

############### Files ###############

def LoadDf(subfolder, measureCols, vacName):
    df = pd.read_csv(subfolder + 'infect_' + vacName + '.csv', 
                    index_col=list(range(3 + len(measureCols))),
                    header=list(range(1)))
    
    df.columns.name = 'day'
    df.columns = df.columns.astype(float).astype(int)
    df = df.groupby(level=ListRemove(list(df.index.names), 'age'), axis=0).sum()
    return df
   
    
def LoadMainData(subfolder, measureCols, vacName):
    df = pd.read_csv(subfolder + 'infect_' + vacName + '.csv', 
                    index_col=list(range(2 + len(measureCols))),
                    header=list(range(1)))
    
    df.columns.name = 'day'
    df.columns = df.columns.astype(float).astype(int)
    return df
    

############### Processing ###############

def RestrictDf(df, dayStart, dayEnd):
    df = df[list(range(dayStart, dayEnd))]
    return df

    
############### Mains ###############

def QuestionPrepare(subfolder, dataPath, measureCols):
    print('loading DF')
    dfVac = LoadDf(dataPath, measureCols, 'vac')
    dfNoVac = LoadDf(dataPath, measureCols, 'noVac')
    OutputToFile(dfVac + dfNoVac, subfolder + '/Question_process/' + 'infect_daily')
    
    
def QuestionOne(subfolder, dataPath, measureCols):
    df = LoadMainData(dataPath, measureCols, 'daily')
    df = RestrictDf(df, 182, 365)
    OutputToFile(df.describe(), subfolder + '/Question_process/' + 'describeDays')
    
#QuestionPrepare(dataDir, dataDir + '/Mort_process/', measureCols_global)
QuestionOne(dataDir, dataDir + '/Question_process/', measureCols_global)