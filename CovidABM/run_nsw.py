# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 12:16:11 2021

@author: wilsonte
"""
import pandas as pd
import numpy as np

from processNetlogoOutput import DoAbmProcessing
from aggregateSpartan import DoSpartanAggregate
from processToMortHosp import PreProcessMortHosp, FinaliseMortHosp, DrawMortHospDistributions
from processToMortHosp import MakeCaseHeatmaps, MakeMortHospHeatmapRange
from makeHeatmaps import MakeStagesHeatmap
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

measureCols_raw = [
	'r0_range',
	'compound_essential',
	'data_suffix',
	'param_vac_rate_mult',
	'param_policy',
]
measureCols = [
	'R0',
	'Essential',
	'Rollout',
	'VacRate',
	'Policy',
]

heatmapStructure = {
	'index_rows' : ['Policy', ],
	'index_cols' : ['Rollout', ],
	'sort_rows' : [
		['Policy', {
			'Stage3' : 'a',
			'Stage3b' : 'b',
			'Stage4' : 'c',
		}],
	], 
	'sort_cols' : [
		['Rollout', {
			'BAU' : 'a',
			'INT' : 'b',
			'AZ_25' : 'c',
			'AZ_50' : 'c',
		}],
	]
}

defaultValues = [
	{
		'R0' : 6,
		'Essential' : 'Extreme',
		'Rollout' : 'BAU',
		'Policy' : 'Stage3b',
		'VacRate' : 0.5,
	},
	{
		'R0' : 6,
		'Essential' : 'Extreme',
		'Rollout' : 'INT',
		'Policy' : 'Stage3b',
		'VacRate' : 0.5,
	},
	{
		'R0' : 6,
		'Essential' : 'Extreme',
		'Rollout' : 'AZ_25',
		'Policy' : 'Stage3b',
		'VacRate' : 0.5,
	},
	{
		'R0' : 6,
		'Essential' : 'Extreme',
		'Rollout' : 'AZ_50',
		'Policy' : 'Stage3b',
		'VacRate' : 0.5,
	},
]

def indexRenameFunc(chunk):
	index = chunk.index.to_frame()
	#index['R0'] = index['global_transmissibility_out'].apply(lambda x: 3.75 if x < 0.61333 else (4.17 if x < 0.681666 else 4.58))
	
	index['data_suffix'] = index['data_suffix'].replace({
		'_bau.csv' : 'BAU',
		'_int.csv' : 'INT',
		'_az_25.csv' : 'AZ_25',
		'_az_50.csv' : 'AZ_50',
	})
	
	renameCols = {measureCols_raw[i] : measureCols[i] for i in range(len(measureCols))}
	index = index.rename(columns=renameCols)
	
	chunk.index = pd.MultiIndex.from_frame(index)
	return chunk

# R0_range param_policy VacKids param_vacincurmult param_vac_uptake
favouriteParams = [5, 'ME_TS_LS', 'No', 5, 0.7]

#dataDir = '2021_05_04'
dataDir = 'NSW/2021_08_05'
rawDataDir = dataDir + '/ABM_out/'

dryRun = False
preChecks = False
aggregateSpartan = False
doDraws = False
makeOutput = True

if preChecks:
	DoPreProcessChecks(dataDir, rawDataDir, indexRenameFunc, measureCols, measureCols_raw, defaultValues, firstOnly=dryRun)

oldNonSpartan = False
if oldNonSpartan:
	DoAbmProcessing(dataDir, rawDataDir, indexRenameFunc, measureCols, measureCols_raw, firstOnly=dryRun, day_override=728)
	#PreProcessMortHosp(dataDir, measureCols)

if aggregateSpartan:
	DoSpartanAggregate(dataDir, measureCols)

if doDraws:
	DrawMortHospDistributions(dataDir, measureCols, drawCount=100, padMult=40)
	FinaliseMortHosp(dataDir, measureCols)

if makeOutput:
	MakeMortHospHeatmapRange(dataDir, measureCols, heatmapStructure, 'weeklyAgg', 0, 100/7, describe=True, deathLag=2)
	MakeMortHospHeatmapRange(dataDir, measureCols, heatmapStructure, 'tendayAgg', 0, 10, describe=True, deathLag=0)

	MakeStagesHeatmap(dataDir, measureCols, heatmapStructure, 0, 364, describe=True)

#DoProcessingForPMSLT(dataDir, measureCols, months=24)
#DoProcessingForReport(dataDir, measureCols, table5Rows, 'param_vac_uptake', months=24)

filterIndex = [
	('R0', 6),
	('Essential', 'Extreme'),
	('Rollout', 'BAU'),
	('VacRate', 0.5),
]

#MakePrettyGraphs(
#	dataDir, 'processed_case14_daily', measureCols,
#	'Policy', mean=False, filterIndex=filterIndex, timesteps=30)

#MakeDailyGraphs(dataDir, 'processed_case14', measureCols, 'VacRate', mean=False, filterIndex=filterIndex)
#MakePrettyGraphs(dataDir, 'processed_stage', measureCols, 'param_policy')
#MakeFavouriteGraph(dataDir, 'processed_stage', measureCols, favouriteParams)
#MakeFavouriteGraph(dataDir, 'infect_unique', measureCols, favouriteParams)

#ProcessPMSLTResults(dataDir, measureCols, heatmapStructure, healthPerspectiveRows)