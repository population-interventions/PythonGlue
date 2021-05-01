# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 12:14:53 2021

@author: wilsonte
"""

import pandas as pd
import os

fileCreated = {}
HEAD_MODE = True


def MakePath(path):
    if '/' not in path:
        return
    out_folder = os.path.dirname(path)
    if not os.path.exists(out_folder):
        MakePath(out_folder)
        os.mkdir(out_folder)


def OutputToFile(df, path, index=True):
    # Called like this. Splits each random seed into its own file.
    #for value in chunk.index.unique('rand_seed'):
    #    OutputToFile(chunk.loc[value], filename, value)
    fullFilePath = path + '.csv'
    MakePath(path)
    
    if fileCreated.get(fullFilePath):
        # Append
        df.to_csv(fullFilePath, mode='a', header=False, index=index)
    else:
        fileCreated[fullFilePath] = True
        df.to_csv(fullFilePath, index=index) 
        if HEAD_MODE:
            df.head(100).to_csv(path + '_head' + '.csv', index=index) 


def SplitNetlogoList(chunk, cohorts, name, outputName):
    split_names = [outputName + str(i) for i in range(0, cohorts)]
    chunk[split_names] = chunk[name].str.replace('\[', '').str.replace('\]', '').str.split(' ', expand=True)
    chunk = chunk.drop(name, axis=1)
    return chunk
    
  
def SplitNetlogoNestedList(chunk, cohorts, days, colName, name):
    split_names = [(name, j, i) for j in range(0, days) for i in range(0, cohorts)]
    df = chunk[colName].str.replace('\[', '').str.replace('\]', '').str.split(' ', expand=True)
    df.columns = pd.MultiIndex.from_tuples(split_names, names=['metric', 'day', 'cohort'])
    return df


def AddFiles(outputName, fileList, index=1, header=1):
    first = True
    for fileName in fileList:
        if first:
            first = False
            df = pd.read_csv(fileName + '.csv',
                             index_col=list(range(index)),
                             header=list(range(header)))
        else:
            df = df + pd.read_csv(fileName + '.csv',
                                  index_col=list(range(index)),
                                  header=list(range(header)))
    OutputToFile(df, outputName)


def ToHeatmap(df, index_rows, index_cols, sort_rows=[], sort_cols=[]):
    if df.index.name != None:
        df = df.reset_index()
    
    df['_sort_row'] = ''
    for value in sort_rows:
        df['_sort_row'] = df['_sort_row'] + df[value[0]].replace(value[1]).astype(str)
    df['_sort_col'] = ''
    for value in sort_cols:
        df['_sort_col'] = df['_sort_col'] + df[value[0]].replace(value[1]).astype(str)
        
    df = df.set_index(['_sort_row', '_sort_col'] + index_rows + index_cols)
    df = df.unstack(['_sort_col'] + index_cols)
    df = df.sort_index(axis=0, level=0)
    df = df.sort_index(axis=1, level=0)
    
    df.columns = df.columns.droplevel(level=1)
    df.index = df.index.droplevel(level=0)
    return df
