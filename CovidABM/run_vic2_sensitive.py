# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 12:16:11 2021

@author: wilsonte
"""
import pandas as pd
import numpy as np

from processNetlogoOutput import DoAbmProcessing
from makeHeatmaps import MakeHeatmaps
from makeGraphs import MakePrettyGraphs, MakeFavouriteGraph
from processedOutputToPMSLT import DoProcessingForPMSLT
from processedOutputToPMSLT import GetAggregates
from processedOutputToReport import DoProcessingForReport
from processPMSLTOutput import ProcessPMSLTResults

table5Rows = [
    [False, False],
    ['mask_efficacy_mult', [0, 1]],
    ['param_vacincurmult', [1.28, 5.12]],
    ['param_trace_mult', [0, 0.5, 1]],
    ['param_vac_uptake', [0, 0.5, 0.7, 0.9]],
    ['compound_param', ['None', 'Hetro_Test']],
]

healthPerspectiveRows = [
    [False, False],
    ['mask_efficacy_mult', [0, 1]],
    ['param_vacincurmult', [1.28, 5.12]],
    ['param_trace_mult', [0, 0.5, 1]],
    ['param_vac_uptake', [0, 0.5, 0.7, 0.9]],
    ['compound_param', ['None', 'Hetro_Test']],
]

measureCols_raw = ['mask_efficacy_mult', 'param_vacincurmult', 'param_trace_mult', 'compound_param', 'param_vac_uptake']
measureCols =  ['HetoMult', 'Masks', 'Trace', 'VacUptake', 'IncursionMult'] 
        
heatmapStructure = {
    'index_rows' : ['HetoMult', 'Masks', 'Trace'],
    'index_cols' : ['VacUptake', 'IncursionMult'],
    'sort_rows' : [
        ['HetoMult', {
            1 : 'a',
            0.2 : 'b',
        }],
        ['Masks', {
            'Yes' : 'a',
            'No' : 'b',
        }],
        ['Trace', {
            'Full' : 'a',
            'Half' : 'b',
            'Off' : 'c',
        }],
    ], 
    'sort_cols' : [
        ['VacUptake', {
            0.9 : 'a',
            0.7 : 'b',
            0.5 : 'c',
            0 : 'd',
        }],
        ['IncursionMult', {
            1.28 : 'a',
            5.12 : 'b',
        }],
    ]
}

def indexRenameFunc(chunk):
    index = chunk.index.to_frame()
    index['compound_param'] = index['compound_param'].replace({
        'None' : 1,
        'Hetro_Test' : 0.2,
    })
    index['mask_efficacy_mult'] = index['mask_efficacy_mult'].replace({
        0 : 'No',
        1 : 'Yes',
    })
    index['param_trace_mult'] = index['param_trace_mult'].replace({
        0 : 'Off',
        0.5 : 'Half',
        1 : 'Full',
    })
    index = index.rename(columns={
        'compound_param' : 'HetoMult',
        'mask_efficacy_mult' : 'Masks',
        'param_trace_mult' : 'Trace',
        'param_vac_uptake' : 'VacUptake',
        'param_vacincurmult' : 'IncursionMult'
    })
    
    chunk.index = pd.MultiIndex.from_frame(index)
    return chunk

# R0_range param_policy VacKids param_vacincurmult param_vac_uptake
favouriteParams = [4.5, 'ME_TS_LS', 'No', 12.5, 0.7]

#dataDir = '2021_05_04'
dataDir = 'Vic2/2021_06_25_sensitive'

DoAbmProcessing(dataDir, indexRenameFunc, measureCols, measureCols_raw)
MakeHeatmaps(dataDir, measureCols, heatmapStructure, dropMiddleValues=False)
#DoProcessingForPMSLT(dataDir, measureCols, months=24)
#DoProcessingForReport(dataDir, measureCols, table5Rows, 'param_vac_uptake', months=24)

#MakePrettyGraphs(dataDir, 'infect_unique', measureCols, 'param_policy', median=False)
#MakePrettyGraphs(dataDir, 'processed_stage', measureCols, 'param_policy')
#MakeFavouriteGraph(dataDir, 'processed_stage', measureCols, favouriteParams)
#MakeFavouriteGraph(dataDir, 'infect_unique', measureCols, favouriteParams)

#ProcessPMSLTResults(dataDir, measureCols, heatmapStructure, healthPerspectiveRows)