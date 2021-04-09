
import pandas as pd
import numpy as np


def FillAges(df, ageRange):
    df = df.reset_index()
    crossDf = pd.DataFrame({'extra' : range(ageRange), 'cross_key' : 1})
    df['cross_key'] = 1
    df = df.merge(crossDf, how='outer', on='cross_key').drop('cross_key', axis=1)
    df['age'] = df['age'] + df['extra']
    df = df.drop('extra', axis=1)
    df = df.set_index(['age', 'sex'])
    
    for age in range(111):
        if age not in df.index:
            prev = df.loc[[age - 1]]
            prev = prev.reset_index()
            prev['age'] = age
            prev = prev.set_index(['age', 'sex'])
            df = df.append(prev)
    
    df = df.sort_index()
    df = df.sort_index(axis=1)
    return df
