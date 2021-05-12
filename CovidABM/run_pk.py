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

#dataDir = '2021_05_04'
dataDir = '2021_05_10'

measureCols_raw =  ['param_policy', 'param_vac_rate_mult', 'param_final_phase',
        'variant_transmiss_growth', 'param_vac_tran_reduct', 'vac_variant_eff_prop']

measureCols =  ['param_policy', 'RolloutMonths', 'VacKids',
        'VacEfficacy', 'VacEff_VarMult', 'Var_R0_mult'] 

#DoAbmProcessing(dataDir, measureCols, measureCols_raw)
#MakeHeatmaps(dataDir, measureCols)
#DoProcessingForPMSLT(dataDir, measureCols, months=24)
#DoProcessingForReport(dataDir, measureCols, table5Rows, months=24)

#MakeFullGraphs(dataDir, measureCols)
MakeFavouriteGraph(dataDir, measureCols)

#ProcessPMSLTResults(dataDir, measureCols, healthPerspectiveRows)