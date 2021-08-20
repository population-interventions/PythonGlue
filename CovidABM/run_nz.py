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
from processToMortHosp import MakeMortHospHeatmapRange
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

heatmapStructure = {
	'index_rows' : ['Policy', 'R0', 'AgeLimit'],
	'index_cols' : ['VacUptake', 'IncurRate'],
	'sort_rows' : [
		['Policy', {
			'AggressElim' : 'a',
			'ModerateElim' : 'b',
		}],
		['R0', {
			6.5 : 'a',
		}],
		['AgeLimit', {
			'5+' : 'a',
			'10+' : 'b',
			'16+' : 'c',
		}],
	], 
	'sort_cols' : [
		['VacUptake', {
			'95%' : 'a',
			'85%' : 'b',
			'70%' : 'c',
		}],
		['IncurRate', {
			0.5 : 'a',
			1 : 'b',
			5 : 'c',
			10 : 'd',
		}],
	]
}

defaultValues = [
	{
		'R0' : 6,
		'Policy' : 'ME_TS_LS',
		'Rollout' : 'INT',
		'VacUptake' : 0.8,
		'Kids' : 'Yes',
		'IncurRate' : 5,
	},
]
measureCols_raw = [
	'r0_range',
	'param_policy',
	'data_suffix',
	'data_suffix_2',
	'param_vacincurmult',
]
measureCols = [
	'R0',
	'Policy',
	'VacUptake',
	'AgeLimit',
	'IncurRate',
]

def indexRenameFunc(chunk):
	index = chunk.index.to_frame()
	#index['R0'] = index['global_transmissibility_out'].apply(lambda x: 3.75 if x < 0.61333 else (4.17 if x < 0.681666 else 4.58))
	
	#index['data_suffix'] = index['data_suffix'].replace({
	#	'_bau.csv' : 'BAU',
	#	'_int.csv' : 'INT',
	#	'_az_25.csv' : 'AZ_25',
	#	'_az_50.csv' : 'AZ_50',
	#})
	index['data_suffix'] = index['data_suffix'].replace({
		'_70' : '70%',
		'_85' : '85%',
		'_95' : '95%',
	})
	index['data_suffix_2'] = index['data_suffix_2'].replace({
		'_15.csv' : '16+',
		'_10.csv' : '10+',
		'_5.csv' : '5+',
	})
	
	renameCols = {measureCols_raw[i] : measureCols[i] for i in range(len(measureCols))}
	index = index.rename(columns=renameCols)
	
	chunk.index = pd.MultiIndex.from_frame(index)
	return chunk



# R0_range param_policy VacKids param_vacincurmult param_vac_uptake
favouriteParams = [5, 'ME_TS_LS', 'No', 5, 0.7]

#dataDir = '2021_05_04'
dataDir = 'NZ/2021_08_19'
rawDataDir = dataDir + '/outputs_snowy/'
day_override = 574

dryRun = False
preChecks = False
aggregateSpartan = True
doDraws = True
makeOutput = True

if preChecks:
	DoPreProcessChecks(
		dataDir, rawDataDir, indexRenameFunc, measureCols, measureCols_raw,
		defaultValues, firstOnly=dryRun)

oldNonSpartan = False
if oldNonSpartan:
	DoAbmProcessing(dataDir, rawDataDir, indexRenameFunc, measureCols, measureCols_raw, firstOnly=dryRun, day_override=day_override)
	#PreProcessMortHosp(dataDir, measureCols)

if aggregateSpartan:
	DoSpartanAggregate(dataDir, measureCols, arraySize=20)

if doDraws:
	DrawMortHospDistributions(dataDir, measureCols, drawCount=100, padMult=1)
	FinaliseMortHosp(dataDir, measureCols)

if makeOutput:
	MakeMortHospHeatmapRange(dataDir, measureCols, heatmapStructure, 'weeklyAgg', 0, 52, aggSize=7, describe=True)

	MakeStagesHeatmap(dataDir, measureCols, heatmapStructure, 0, 364, describe=True)

#DoProcessingForPMSLT(dataDir, measureCols, months=24)
#DoProcessingForReport(dataDir, measureCols, table5Rows, 'param_vac_uptake', months=24)

filterIndex = [
	('R0', 6.5),
	('Essential', 'Extreme'),
	('Rollout', 'BAU'),
	('VacRate', 0.5),
]

#MakeDailyGraphs(dataDir, 'processed_case14', measureCols, 'VacRate', mean=False, filterIndex=filterIndex)
#MakePrettyGraphs(dataDir, 'processed_case_daily', measureCols, 'Policy', mean=False, filterIndex=filterIndex)
#MakePrettyGraphs(dataDir, 'processed_stage', measureCols, 'param_policy')
#MakeFavouriteGraph(dataDir, 'processed_stage', measureCols, favouriteParams)
#MakeFavouriteGraph(dataDir, 'infect_unique', measureCols, favouriteParams)

#ProcessPMSLTResults(dataDir, measureCols, heatmapStructure, healthPerspectiveRows)