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

table5Rows = [
    [False, False],
    ['r0_range', [4.5, 4.833, 5.166]],
    ['param_policy', ['ME_ME_ME', 'ME_ME_TS', 'ME_ME_LS', 'ME_TS_LS']],
    ['param_vacincurmult', [0.02, 0.08, 0.32, 1.28, 5.12]],
    ['VacKids', ['No', 'Yes']],
]

healthPerspectiveRows = [
    [False, False],
    ['r0_range', [4.5, 4.833, 5.166]],
    ['param_policy', ['ME_ME_ME', 'ME_ME_TS', 'ME_ME_LS', 'ME_TS_LS']],
    ['param_vacincurmult', [0.02, 0.08, 0.32, 1.28, 5.12]],
    ['VacKids', ['No', 'Yes']],
]

measureCols_raw = ['r0_range', 'policy_pipeline', 'param_final_phase', 'param_vacincurmult', 'param_vac_uptake']
measureCols =  ['r0_range', 'policy_pipeline', 'VacKids', 'param_vacincurmult', 'param_vac_uptake'] 

heatmapStructure = {
    'index_rows' : ['policy_pipeline', 'r0_range', 'VacKids'],
    'index_cols' : ['param_vac_uptake', 'param_vacincurmult'],
    'sort_rows' : [
        ['policy_pipeline', {
            'ME_ME_TS' : 'b',
            'ME_TS_LS' : 'd',
            'ME_TS_BS' : 'e',
        }],
        ['r0_range', {
            5 : 'a',
            6 : 'b',
        }],
        ['VacKids', {
            'Yes' : 'a',
            'No' : 'b',
        }],
    ], 
    'sort_cols' : [
        ['param_vac_uptake', {
            0.9 : 'a',
            0.8 : 'b',
            0.7 : 'c',
            0.6 : 'd',
            0.5 : 'e',
        }],
        ['param_vacincurmult', {
            0.2 : 'a',
            1 : 'b',
            5 : 'c',
            25 : 'd',
        }],
    ]
}

def indexRenameFunc(chunk):
    index = chunk.index.to_frame()
    #index['R0'] = index['global_transmissibility_out'].apply(lambda x: 3.75 if x < 0.61333 else (4.17 if x < 0.681666 else 4.58))
    index['param_final_phase'] = index['param_final_phase'].replace({
        3 : 'Yes',
        2 : 'No',
    })
    index = index.rename(columns={
        'param_final_phase' : 'VacKids',
    })
    
    chunk.index = pd.MultiIndex.from_frame(index)
    return chunk

# R0_range param_policy VacKids param_vacincurmult param_vac_uptake
favouriteParams = [5, 'ME_TS_LS', 'No', 5, 0.7]

#dataDir = '2021_05_04'
dataDir = 'Vic2/2021_07_05'

#DoAbmProcessing(dataDir, indexRenameFunc, measureCols, measureCols_raw)

#PreProcessMortHosp(dataDir, measureCols)
#DrawMortHospDistributions(dataDir, measureCols)
#FinaliseMortHosp(dataDir, measureCols)
MakeMortHospHeatmaps(dataDir, measureCols, heatmapStructure)

#MakeHeatmaps(dataDir, measureCols, heatmapStructure, dropMiddleValues=False)
#DoProcessingForPMSLT(dataDir, measureCols, months=24)
#DoProcessingForReport(dataDir, measureCols, table5Rows, 'param_vac_uptake', months=24)

#MakePrettyGraphs(dataDir, 'infect_unique', measureCols, 'param_policy', median=False)
#MakePrettyGraphs(dataDir, 'processed_stage', measureCols, 'param_policy')
#MakeFavouriteGraph(dataDir, 'processed_stage', measureCols, favouriteParams)
#MakeFavouriteGraph(dataDir, 'infect_unique', measureCols, favouriteParams)

#ProcessPMSLTResults(dataDir, measureCols, heatmapStructure, healthPerspectiveRows)