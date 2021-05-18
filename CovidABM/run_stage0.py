# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 12:16:11 2021

@author: wilsonte
"""

from processNetlogoOutput import DoAbmProcessing
from makeHeatmaps import MakeHeatmaps
from makeGraphs import MakeStage0Graphs
from processedOutputToPMSLT import DoProcessingForPMSLT
from processedOutputToPMSLT import GetAggregates
from processedOutputToReport import DoProcessingForReport
from processPMSLTOutput import ProcessPMSLTResults

table5Rows = [
    [False, False],
    ['R0', [2.5, 3]],
]

dataDir = '2021_05_12_stage0'

measureCols_raw =  ['param_policy', 'param_vac_rate_mult', 'param_final_phase',
        'variant_transmiss_growth', 'param_vac_tran_reduct', 'vac_variant_eff_prop']

measureCols =  ['param_policy', 'RolloutMonths', 'VacKids',
        'VacEfficacy', 'VacEff_VarMult', 'Var_R0_mult'] 

#DoAbmProcessing(dataDir, measureCols, measureCols_raw)
#DoProcessingForPMSLT(dataDir, measureCols, months=12)
DoProcessingForReport(dataDir, measureCols, table5Rows, months=12)

MakeStage0Graphs(dataDir, measureCols)

#ProcessPMSLTResults(dataDir, measureCols, table5Rows)