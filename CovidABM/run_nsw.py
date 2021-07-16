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
from makeGraphs import MakePrettyGraphs, MakeFavouriteGraph
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

measureCols_raw = ['param_policy']
measureCols =  ['param_policy'] 

heatmapStructure = {
    'index_rows' : ['param_policy'],
    'index_cols' : ['sympt_present_prop'],
    'sort_rows' : [
        ['param_policy', {
            'Stage2' : 'a',
            'Stage3' : 'b',
            'Stage4' : 'c',
        }],
    ], 
    'sort_cols' : [
        ['sympt_present_prop', {
            0.5 : 'a',
            0.3 : 'b',
        }],
    ]
}

filterIndex = [
    ('sympt_present_prop', 0.5),
]

def indexRenameFunc(chunk):
    return chunk

# R0_range param_policy VacKids param_vacincurmult param_vac_uptake
favouriteParams = [5, 'ME_TS_LS', 'No', 5, 0.7]

#dataDir = '2021_05_04'
dataDir = 'NSW/2021_07_15a'

#DoPreProcessChecks(dataDir)
DoAbmProcessing(dataDir, indexRenameFunc, measureCols, measureCols_raw, day_override=364)

#PreProcessMortHosp(dataDir, measureCols)
#DrawMortHospDistributions(dataDir, measureCols)
#FinaliseMortHosp(dataDir, measureCols)
#MakeMortHospHeatmaps(dataDir, measureCols, heatmapStructure, years=1)

#MakeHeatmaps(dataDir, measureCols, heatmapStructure, windowCount=1, dropMiddleValues=False)
#DoProcessingForPMSLT(dataDir, measureCols, months=12)
#DoProcessingForReport(dataDir, measureCols, table5Rows, 'param_vac_uptake', months=12)

#MakePrettyGraphs(dataDir, 'infect_unique', measureCols, 'param_policy', median=False, filterIndex=filterIndex)
#MakePrettyGraphs(dataDir, 'processed_stage', measureCols, 'param_policy')
#MakeFavouriteGraph(dataDir, 'processed_stage', measureCols, favouriteParams)
#MakeFavouriteGraph(dataDir, 'infect_unique', measureCols, favouriteParams)

#ProcessPMSLTResults(dataDir, measureCols, heatmapStructure, healthPerspectiveRows)