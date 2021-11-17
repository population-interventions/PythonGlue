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
from processToMortHosp import MakeMortHospHeatmapRange, MakeIcuHeatmaps
from makeHeatmaps import MakeStagesHeatmap, MakeComparisionHeatmap
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
	'index_rows' : ['Stage', 'VacEaseStage'],
	'index_cols' : ['VacEaseSchoolOpen', 'VacEaseEveryone'],
	'base_value' : {
		'Stage' : 3.25,
		'VacEaseSchoolOpen' : 0,
	},
	'sort_rows' : [
		['Stage', {
			3.25 : 'a',
		}],
		['VacEaseStage', {
			'2a_mask3a' : 'a',
			'1b_mask2a' : 'b',
			'1b' : 'c',
		}],
	], 
	'sort_cols' : [
		['VacEaseSchoolOpen', {
			0 : 'a',
			1 : 'b',
		}],
		['VacEaseEveryone', {
			0 : 'a',
			1 : 'b',
		}],
	]
}

defaultValues = [
	{
		'Stage' : 3.25,
		'VacEaseSchoolOpen' : 0,
		'VacEaseStage' : '2a_mask3a',
		'VacEaseEveryone' : 1,
	},
]

heatAges = [
	#[0, 15],
	#[15, 25],
	#[25, 35],
	#[35, 45],
	#[45, 55],
	#[55, 65],
	#[65, 75],
	#[75, 85],
	#[85, 95],
	#[95, 110],
	[0, 110],
]

measureCols_raw = [
	'cont_stage',
	'vac_ease_schools_open',
	'vac_ease_stage',
	'vac_ease_everyone',
]
measureCols = [
	'Stage',
	'VacEaseSchoolOpen',
	'VacEaseStage',
	'VacEaseEveryone',
]

def indexRenameFunc(chunk):
	index = chunk.index.to_frame()
	#index['R0'] = index['global_transmissibility_out'].apply(lambda x: 3.75 if x < 0.61333 else (4.17 if x < 0.681666 else 4.58))

	renameCols = {measureCols_raw[i] : measureCols[i] for i in range(len(measureCols))}
	index = index.rename(columns=renameCols)
	
	chunk.index = pd.MultiIndex.from_frame(index)
	return chunk


# R0_range param_policy VacKids param_vacincurmult param_vac_uptake
favouriteParams = [5, 'ME_TS_LS', 'No', 5, 0.7]

#dataDir = '2021_05_04'
dataDir = 'NSW/2021_09_22'
rawDataDir = dataDir + '/outputs_snowy/'
day_override = False

compareHeatmap = 'weeklyAgg_infect_from_30_to_82_age_0_110_total_percentile_050'
compareStages = 'stageAbove_2_from_210_to_574_percentile_050'

dryRun = False
preChecks = False
aggregateSpartan = True
doDraws = False
doFinaliseCohortAgg = False
makeOutput = False
outputStages = False
processIcu = False
makeComparison = False

if preChecks:
	DoPreProcessChecks(
		dataDir, rawDataDir, indexRenameFunc, measureCols, measureCols_raw,
		defaultValues, firstOnly=dryRun)

oldNonSpartan = False
if oldNonSpartan:
	DoAbmProcessing(dataDir, rawDataDir, indexRenameFunc, measureCols, measureCols_raw, firstOnly=dryRun, day_override=day_override)
	#PreProcessMortHosp(dataDir, measureCols)

if aggregateSpartan:
	DoSpartanAggregate(dataDir, measureCols, doLong=True, arraySize=25)

if doDraws:
	DrawMortHospDistributions(dataDir, measureCols, drawCount=100, padMult=60)

if doFinaliseCohortAgg:
	FinaliseMortHosp(dataDir, measureCols, heatAges)

if makeOutput:
	MakeMortHospHeatmapRange(dataDir, measureCols, heatAges, heatmapStructure, 'weeklyAgg', 0, 6, aggSize=7, describe=True)
	MakeMortHospHeatmapRange(dataDir, measureCols, heatAges, heatmapStructure, 'weeklyAgg', 0, 11, aggSize=7, describe=True)
	MakeMortHospHeatmapRange(dataDir, measureCols, heatAges, heatmapStructure, 'weeklyAgg', 0, 20, aggSize=7, describe=True)
	MakeMortHospHeatmapRange(dataDir, measureCols, heatAges, heatmapStructure, 'weeklyAgg', 11, 9, aggSize=7, describe=True)

if outputStages:
	MakeStagesHeatmap(dataDir, measureCols, heatmapStructure, 0, 210, describe=True)
	MakeStagesHeatmap(dataDir, measureCols, heatmapStructure, 210, 364, describe=True)
	MakeStagesHeatmap(dataDir, measureCols, heatmapStructure, 0, 574, describe=True)

	MakeStagesHeatmap(dataDir, measureCols, heatmapStructure, 182, 28, describe=True)
	MakeStagesHeatmap(dataDir, measureCols, heatmapStructure, 210, 364, describe=True)

if processIcu:
	MakeIcuHeatmaps(dataDir, measureCols, heatmapStructure, 0, 6, describe=True)
	MakeIcuHeatmaps(dataDir, measureCols, heatmapStructure, 0, 11, describe=True)
	MakeIcuHeatmaps(dataDir, measureCols, heatmapStructure, 0, 63, describe=True)
	MakeIcuHeatmaps(dataDir, measureCols, heatmapStructure, 11, 52, describe=True)

if makeComparison:
	MakeComparisionHeatmap(dataDir, heatmapStructure, compareHeatmap)
	MakeComparisionHeatmap(dataDir, heatmapStructure, compareHeatmap, divide=False)
	MakeComparisionHeatmap(dataDir, heatmapStructure, compareStages, divide=False)

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