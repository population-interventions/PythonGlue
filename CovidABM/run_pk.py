# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 12:16:11 2021

@author: wilsonte
"""

from processNetlogoOutput import DoAbmProcessing
from makeHeatmaps import MakeHeatmaps
from makeGraphs import MakeFullGraphs, MakeFavouriteGraph
from processedOutputToPMSLT import DoProcessingForPMSLT
from processedOutputToPMSLT import GetAggregates
from processedOutputToReport import DoProcessingForReport
from processPMSLTOutput import ProcessPMSLTResults

table5Rows = [
    [False, False],
    ['R0', [2.5, 3]],
    ['param_policy', ['ModerateSupress', 'ModerateSupress_No_4'], {'ModerateSupress' : True}],
    ['VacEfficacy', [0.95, 0.875, 0.75]],
    ['Var_R0_mult', [1.3, 1.45, 1.6]],
    ['VacEff_VarMult', [0.95, 0.8]],
    ['VacKids', ['No', 'Yes']],
]

healthPerspectiveRows = [
    [False, False],
    ['R0', [2.5, 3]],
    ['param_policy', ['ModerateSupress', 'ModerateSupress_No_4']],
    ['VacEfficacy', [0.95, 0.875, 0.75]],
    ['Var_R0_mult', [1.3, 1.45, 1.6]],
    ['VacEff_VarMult', [0.95, 0.8]],
    ['VacKids', ['No', 'Yes']],
]

heatmapStructure = {
    'index_rows' : ['param_policy', 'R0', 'Var_R0_mult', 'VacKids'],
    'index_cols' : ['VacEfficacy', 'VacEff_VarMult'],
    'sort_rows' : [
        ['param_policy', {
            'ModerateSupress_No_4' : 'b',
            'ModerateSupress' : 'a',
        }],
        ['R0', {
            2.5 : 'a',
            3 : 'b',
        }],
        ['Var_R0_mult', {
            1.3 : 'a',
            1.45 : 'b',
            1.6 : 'c',
        }],
        ['VacKids', {
            'Yes' : 'a',
            'No' : 'b',
        }],
    ], 
    'sort_cols' : [
        ['VacEfficacy', {
            0.75 : 'c',
            0.875 : 'b',
            0.95 : 'a',
        }],
        ['VacEff_VarMult', {
            0.8 : 'b',
            0.95 : 'a',
        }],
    ]
}

def indexRenameFunc(chunk):
    index = chunk.index.to_frame()
    index['R0'] = index['global_transmissibility'].apply(lambda x: 2.5 if x < 0.3 else 3)
    index['param_final_phase'] = index['param_final_phase'].replace({
        -1 : 'Yes',
        5 : 'No',
    })
    index['param_vac_rate_mult'] = index['param_vac_rate_mult'].replace({
        0.75 : 16,
        1 : 12,
        1.5 : 8
    })
    index = index.rename(columns={
        'param_final_phase' : 'VacKids',
        'param_vac_rate_mult' : 'RolloutMonths',
        'vac_variant_eff_prop' : 'VacEff_VarMult',
        'variant_transmiss_growth' : 'Var_R0_mult',
        'param_vac_tran_reduct' : 'VacEfficacy',
    })
    
    chunk.index = pd.MultiIndex.from_frame(index)
    return chunk


#dataDir = '2021_05_04'
dataDir = '2021_05_10'

measureCols_raw =  ['global_transmissibility', 'param_policy', 'param_vac_rate_mult', 'param_final_phase',
        'variant_transmiss_growth', 'param_vac_tran_reduct', 'vac_variant_eff_prop']

measureCols =  ['R0', 'param_policy', 'RolloutMonths', 'VacKids',
        'VacEfficacy', 'VacEff_VarMult', 'Var_R0_mult'] 

#DoAbmProcessing(dataDir, indexRenameFunc, measureCols, measureCols_raw)
MakeHeatmaps(dataDir, measureCols, heatmapStructure, dropMiddleValues=False)
#DoProcessingForPMSLT(dataDir, measureCols, months=24)
DoProcessingForReport(dataDir, measureCols, table5Rows, 'RolloutMonths', compareCol=0, months=24)

MakeFullGraphs(dataDir, measureCols)
#MakeFavouriteGraph(dataDir, measureCols)

ProcessPMSLTResults(dataDir, measureCols, heatmapStructure, healthPerspectiveRows)