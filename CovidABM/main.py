# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 12:16:11 2021

@author: wilsonte
"""


from processNetlogoOutput import DoAbmProcessing
from processNetlogoOutput import MakeHeatmaps
from processedOutputToPMSLT import DoProcessingForPMSLT


dataDir = '2021_04_29'
dataDir = '2021_05_01_stage2'

measureCols_raw =  ['param_policy', 'param_vac_rate_mult', 'param_final_phase',
        'variant_transmiss_growth', 'param_vac_tran_reduct', 'vac_variant_eff_prop']

measureCols =  ['param_policy', 'RolloutMonths', 'VacKids',
        'VacEfficacy', 'VacEff_VarMult', 'Var_R0_mult'] 

DoAbmProcessing(dataDir, measureCols, measureCols_raw, day_override=1095)
#MakeHeatmaps(dataDir, measureCols)
DoProcessingForPMSLT(dataDir, measureCols, months=36)
