# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 12:16:11 2021

@author: wilsonte
"""
import pandas as pd
import numpy as np

from processNetlogoOutput import DoAbmProcessing
from processToMortHosp import PreProcessMortHosp, FinaliseMortHosp, MakeMortHospHeatmaps, DrawMortHospDistributions
from makeHeatmaps import MakeHeatmaps
from makeGraphs import MakePrettyGraphs, MakeFavouriteGraph, MakeDailyGraphs
from processedOutputToPMSLT import DoProcessingForPMSLT
from processedOutputToPMSLT import GetAggregates
from processedOutputToReport import DoProcessingForReport
from processPMSLTOutput import ProcessPMSLTResults
from processTraceStyleGraphs import DoPreProcessChecks

table5Rows = [
    [False, False],
    ['param_policy', ['Stage2', 'Stage3', 'Stage4']],
    ['sympt_present_prop', [0.5, 0.3]],
]

healthPerspectiveRows = [
    [False, False],
    ['param_policy', ['Stage2', 'Stage3', 'Stage4']],
    ['sympt_present_prop', [0.5, 0.3]],
]

measureCols_raw = ['param_vac_rate_mult', 'compound_essential', 'input_population_table']
measureCols =  ['VacRate', 'Essential', 'Rollout'] 

heatmapStructure = {
    'index_rows' : ['VacRate'],
    'index_cols' : ['Essential', 'Rollout'],
    'sort_rows' : [
        ['VacRate', {
            0 : 'a',
            0.5 : 'b',
            1 : 'c',
            2 : 'd',
            3 : 'e',
        }],
    ], 
    'sort_cols' : [
        ['Essential', {
            'Normal' : 'a',
            'Extreme' : 'b',
        }],
        ['Rollout', {
            'BAU' : 'a',
            'INT' : 'b',
        }],
    ]
}

filterIndex = [
]

def indexRenameFunc(chunk):
    index = chunk.index.to_frame()
    #index['R0'] = index['global_transmissibility_out'].apply(lambda x: 3.75 if x < 0.61333 else (4.17 if x < 0.681666 else 4.58))
    index['input_population_table'] = index['input_population_table'].replace({
        'input/pop_essential_2007_int.csv' : 'INT',
        'input/pop_essential_2007_bau.csv' : 'BAU',
    })
    index = index.rename(columns={
        'param_vac_rate_mult' : 'VacRate',
        'compound_essential' : 'Essential',
        'input_population_table' : 'Rollout'
    })
    
    chunk.index = pd.MultiIndex.from_frame(index)
    return chunk

# R0_range param_policy VacKids param_vacincurmult param_vac_uptake
favouriteParams = [5, 'ME_TS_LS', 'No', 5, 0.7]

#dataDir = '2021_05_04'
dataDir = 'NSW/2021_07_22'

DoPreProcessChecks(dataDir)
#DoAbmProcessing(dataDir, indexRenameFunc, measureCols, measureCols_raw, day_override=364)

#PreProcessMortHosp(dataDir, measureCols)
#DrawMortHospDistributions(dataDir, measureCols)
#FinaliseMortHosp(dataDir, measureCols)
#MakeMortHospHeatmaps(dataDir, measureCols, heatmapStructure, years=1, describe=True)

#MakeHeatmaps(dataDir, measureCols, heatmapStructure, windowCount=1, dropMiddleValues=False)
#DoProcessingForPMSLT(dataDir, measureCols, months=12)
#DoProcessingForReport(dataDir, measureCols, table5Rows, 'param_vac_uptake', months=12)

#MakeDailyGraphs(dataDir, 'processed_case14', measureCols, 'VacRate', mean=False, filterIndex=filterIndex)
#MakePrettyGraphs(dataDir, 'processed_case14', measureCols, 'VacRate', mean=False, filterIndex=filterIndex)
#MakePrettyGraphs(dataDir, 'processed_stage', measureCols, 'param_policy')
#MakeFavouriteGraph(dataDir, 'processed_stage', measureCols, favouriteParams)
#MakeFavouriteGraph(dataDir, 'infect_unique', measureCols, favouriteParams)

#ProcessPMSLTResults(dataDir, measureCols, heatmapStructure, healthPerspectiveRows)