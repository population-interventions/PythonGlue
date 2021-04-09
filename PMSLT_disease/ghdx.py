
import math
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import os
import re

import utilities


def GetPopulationTable(popFile):
    df = pd.read_csv(popFile + '.csv',
                header=[0],
                index_col=list(range(2)))
    
    df = df.reset_index()
    df = df.rename(columns={'Age (years)' : 'age', 'Sex' : 'sex'})
    df['sex'] = df['sex'].str.lower()
    df = df[(df['sex'] == 'male') | (df['sex'] == 'female')]
    df['age'] = df['age'].str.replace(r'(\d*)-\d*', r'\1').astype(int)
    
    df['age'] = df['age'] + 2
    
    df = df.set_index(['age', 'sex'])
    
    for ageAdd in [5, 10]:
        prev = df.loc[[92 + ageAdd]]
        prev = prev.reset_index()
        prev['age'] = prev['age'] + ageAdd
        prev['population'] = (prev['population']*0.1).astype(int)
        prev = prev.set_index(['age', 'sex'])
        df = df.append(prev)
    
    df = df.sort_index()
    df = df.reset_index()
    return df


############### Output ###############

def ProcessDiseaseTable(popFile, diseaseFile):
    pop_df = GetPopulationTable(popFile)
    
    df = pd.read_csv(diseaseFile + '.csv',
                header=[0])
    
    df['age'] = df['age'].str.replace(r'(\d*) to \d*', r'\1').astype(int).replace({1 : 0})
    df['sex'] = df['sex'].str.lower()
    df = df[(df['sex'] == 'male') | (df['sex'] == 'female')]
    df['measure'] = df['measure'].replace({
        'Prevalence' : 'prev',
        'Incidence' : 'i',
        'Deaths' : 'f',
        'YLDs (Years Lived with Disability)' : 'DR',
    })
    
    df = df.drop(columns=['location', 'cause', 'upper', 'lower', 'year'])
    df = df.set_index(['measure', 'age', 'sex'])
    
    df = df[(df['metric'] == 'Rate')]
    df = df.drop(columns=['metric'])
    df['val'] = df['val'] * (10**-5)
    df = df.unstack('measure')
    df.columns = df.columns.get_level_values('measure')
    df['DR'] = df['DR']/df['prev']
    df['r'] = 0
    
    df = utilities.FillAges(df, 5)
    
    df = df.reset_index()
    df.to_csv('disease_ready/COPD_rates.csv', index=False) 
    
    pop_df.to_csv('disease_ready/base_population.csv', index=False) 
    
    #for name, subDf in df.groupby('measure'):
    #    OutputDisease(name, subDf, pop_df)
    
    
############### Run ###############

ProcessDiseaseTable('COPD_GHDX/pop_au_2019', 'COPD_GHDX/IHME-GBD_2019_DATA-f335e092-1')