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
    ['Masks', ['Yes', 'No']],
    ['HetoMult', [1, 0.2]],
    ['Trace', ['Off', 'Half', 'Full']],
    ['IncursionMult', [1.28, 5.12]],
]

healthPerspectiveRows = [
    [False, False],
    ['Masks', ['Yes', 'No']],
    ['HetoMult', [1, 0.2]],
    ['Trace', ['Off', 'Half', 'Full']],
    ['IncursionMult', [1.28, 5.12]],
]

measureCols_raw = ['param_final_phase', 'param_vacincurmult', 
                   'param_trace_mult', 'compound_mask_param', 
                   'param_vac_uptake', 'r0_range', 
                   'param_force_vaccine', 'policy_pipeline']
measureCols =  ['Masks', 'Trace', 'VacUptake', 'IncursionMult',
                'VacKids', 'R0', 'VacForce', 'Policy'] 
        
heatmapStructure = {
    'index_rows' : ['Policy', 'Masks', 'R0', 'Trace', ],
    'index_cols' : ['VacUptake', 'IncursionMult', 'VacKids', 'VacForce'],
    'sort_rows' : [
        ['Policy', {
            'ME_TS_BS' : 'a',
            'ME_TS_S1' : 'b',
        }],
        ['Masks', {
            'Min100' : 'a',
            'Min50' : 'b',
            'NoMask' : 'c',
        }],
        ['R0', {
            5 : 'a',
            6 : 'b',
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
            0.3 : 'd',
            0 : 'e',
        }],
        ['IncursionMult', {
            1 : 'a',
            5 : 'b',
            25 : 'c',
        }],
        ['VacKids', {
            'Yes' : 'a',
            'No' : 'b',
        }],
        ['VacForce', {
            'Pf' : 'a',
            '-' : 'b',
            'AZ' : 'c',
        }],
    ]
}

def indexRenameFunc(chunk):
    index = chunk.index.to_frame()
    #index['compound_param'] = index['compound_param'].replace({
    #    'None' : 1,
    #    'Hetro_Test' : 0.2,
    #})
    index['param_trace_mult'] = index['param_trace_mult'].replace({
        0 : 'Off',
        0.5 : 'Half',
        1 : 'Full',
    })
    index['param_final_phase'] = index['param_final_phase'].replace({
        2 : 'No',
        3 : 'Yes',
    })
    index['param_force_vaccine'] = index['param_force_vaccine'].replace({
        'Disabled' : '-',
        'AZ' : 'AZ',
        'Pfizer' : 'Pf',
    })
    index = index.rename(columns={
        #'compound_param' : 'HetoMult',
        'compound_mask_param' : 'Masks',
        'param_trace_mult' : 'Trace',
        'param_force_vaccine' : 'VacForce',
        'param_vac_uptake' : 'VacUptake',
        'param_vacincurmult' : 'IncursionMult',
        'param_final_phase' : 'VacKids',
        'policy_pipeline' : 'Policy',
        'r0_range' : 'R0',
    })
    
    chunk.index = pd.MultiIndex.from_frame(index)
    return chunk

# R0_range param_policy VacKids param_vacincurmult param_vac_uptake
favouriteParams = [4.5, 'ME_TS_LS', 'No', 12.5, 0.7]

#dataDir = '2021_05_04'
dataDir = 'Vic2/2021_07_02_sensitive'

DoAbmProcessing(dataDir, indexRenameFunc, measureCols, measureCols_raw)
MakeHeatmaps(dataDir, measureCols, heatmapStructure, dropMiddleValues=False)
#DoProcessingForPMSLT(dataDir, measureCols, months=24)
#DoProcessingForReport(dataDir, measureCols, table5Rows, 'VacUptake', months=24)

#MakePrettyGraphs(dataDir, 'infect_unique', measureCols, 'param_policy', median=False)
#MakePrettyGraphs(dataDir, 'processed_stage', measureCols, 'param_policy')
#MakeFavouriteGraph(dataDir, 'processed_stage', measureCols, favouriteParams)
#MakeFavouriteGraph(dataDir, 'infect_unique', measureCols, favouriteParams)

#ProcessPMSLTResults(dataDir, measureCols, heatmapStructure, healthPerspectiveRows)