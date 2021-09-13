# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 10:22:33 2021

@author: wilsonte
"""

import math
import pandas as pd
import numpy as np
from tqdm import tqdm
import scipy.stats as stats
import pathlib
import time
import os
import gc

from utilities import AddFiles
from utilities import ToHeatmap, CrossIndex
from utilities import OutputToFile, GetCohortData, ListRemove
import utilities as util

nameMap = {
	'hospital' : 'hosp',
	'deaths' : 'mort',
}

############### Preprocessing ###############

def CheckForProblem(df):
	df = df.apply(lambda s: pd.to_numeric(s, errors='coerce').notnull().all())
	if not df.eq(True).all():
		print(df)


def OutputDayAgeAgg(df, outputPrefix, measureCols):
	df = df.groupby(level=list(range(2 + len(measureCols))), axis=0).sum()
	OutputToFile(df, outputPrefix + '_daily')
	

def OutputWeek(df, outputPrefix):
	index = df.columns.to_frame()
	index['week'] = np.floor((index['day'] + 6)/7)
	df.columns = pd.MultiIndex.from_frame(index)
	
	df = df.groupby(level=['week'], axis=1).sum()
	CheckForProblem(df)
	OutputToFile(df, outputPrefix + '_weeklyAgg')


def OutputYear(df, outputPrefix):
	index = df.columns.to_frame()
	index['year'] = np.floor((index['day'])/365)
	df.columns = pd.MultiIndex.from_frame(index)
	
	df = df.groupby(level=['year'], axis=1).sum()
	CheckForProblem(df)
	OutputToFile(df, outputPrefix + '_yearlyAgg')


def ProcessInfectChunk(df, chortDf, outputPrefix):
	df.columns = df.columns.set_levels(df.columns.levels[1].astype(int), level=1)
	df.columns = df.columns.set_levels(df.columns.levels[2].astype(int), level=2)
	df = df.sort_values(['cohort', 'day'], axis=1)
	
	col_index = df.columns.to_frame()
	col_index = col_index.reset_index(drop=True)
	col_index = pd.merge(
		col_index, chortDf,
		on='cohort',
		how='left',
		sort=False)
	col_index = col_index.drop(columns=['atsi', 'morbid'])
	df.columns = pd.MultiIndex.from_frame(col_index)
	
	df = df.groupby(level=[3, 1], axis=1).sum()

	# In the ABM age range 15 represents ages 10-17 while age range 25 is
	# ages 18-30. First redestribute these cohorts so they align with 10 year
	# increments.
	df[15], df[25] = df[15] + df[25]/5, df[25]*4/5

	# Then split the 10 year cohorts in half.
	ageCols = [i*10 + 5 for i in range(10)]
	df = df.stack('day')
	for age in ageCols:
		# TODO, vectorise?
		df[age - 5] = df[age]/2
		df[age] = df[age]/2
	df = df.unstack('day')
	
	# Add extra cohorts missing from ABM
	df = df.sort_index(axis=0)
	df = df.sort_index(axis=1)
	for age in [100 + i*5 for i in range(2)]:
		df1 = df.loc[:, slice(80, 80)].rename(columns={80 : age}, level=0)
		df = df.join(df1)
	
	df = df.stack(level=['age'])
	OutputToFile(df, outputPrefix)
	OutputWeek(df.copy(), outputPrefix)
	OutputYear(df.copy(), outputPrefix)
	return df


def ProcessInfectCohorts(measureCols, filename, cohortFile, outputPrefix):
	cohortData = GetCohortData(cohortFile)
	chunksize = 4 ** 7
	
	for chunk in tqdm(pd.read_csv(
				filename + '.csv', 
				index_col=list(range(2 + len(measureCols))),
				header=list(range(3)),
				dtype={'day' : int, 'cohort' : int},
				chunksize=chunksize),
			total=4):
		df = ProcessInfectChunk(chunk, cohortData, outputPrefix)
		OutputDayAgeAgg(df, outputPrefix, measureCols)


def ProcessInfectionCohorts(subfolder, measureCols):
	print('Processing vaccination infection for MortHosp')
	ProcessInfectCohorts(
		measureCols,
		subfolder + '/ABM_process/processed_infectVac',
		subfolder + '/ABM_process/processed_static',
		subfolder + '/Mort_process/infect_vac')
	print('Processing non-vaccination infection for MortHosp')
	ProcessInfectCohorts(
		measureCols,
		subfolder + '/ABM_process/processed_infectNoVac',
		subfolder + '/ABM_process/processed_static',
		subfolder + '/Mort_process/infect_noVac')


############### Multiplication ###############

def GetEffectsData(file):
	df = pd.read_csv(file + '.csv',
				header=[0])
	df = df.rename(columns={
		'age_start' : 'age',
		'deathPerInfect' : 'mort',
		'icuPerInfect' : 'icu',
		'hospitalPerInfect' : 'hosp',
	})
	df = df.set_index(['vaccine', 'age', 'sex'])
	
	df = df.groupby(level=[0, 1], axis=0).mean()
	return df


def LoadDf(subfolder, measureCols, timeName, vacName):
	df = pd.read_csv(subfolder + 'infect_' + vacName + '_' + timeName + '.csv')
	df = df.set_index(list(df.columns)[0:(3 + len(measureCols))])
	df.columns.name = timeName
	df.columns = df.columns.astype(float).astype(int)
	df = df.unstack(level=ListRemove(list(df.index.names), 'age'))
	return df


def MultiplyByCohortEffect(df, multDf):
	df = df.mul(multDf, axis=0)
	return df


############### Multiplication Uncertainty ###############

def AggregateAgeAndVacDraw(
		dfVac, dfNoVac, cohortEffect, timeName, heatAge, outFile,
		metric, measureCols, vacOnly=False, noVacOnly=False):
	
	if metric != 'infect':
		dfVac = dfVac.mul(cohortEffect.loc[1][metric], axis=0)
		dfNoVac = dfNoVac.mul(cohortEffect.loc[0][metric], axis=0)
	
	if vacOnly:
		dfMetric = dfVac
	elif noVacOnly:
		dfMetric = dfNoVac
	else:
		dfMetric = dfVac + dfNoVac
	#del dfVac
	#del dfNoVac
	#gc.collect()
	
	wantedAges = [i*5 for i in range(int(heatAge[0]/5), int(heatAge[1]/5))]
	
	dfMetric = dfMetric.transpose()
	dfMetric = dfMetric.stack(level=['rand_seed'])
	dfMetric = dfMetric.unstack(level=[timeName])
	dfMetric = dfMetric[wantedAges]
	dfMetric = dfMetric.groupby(level=[timeName], axis=1).sum()
	dfMetric = dfMetric.reorder_levels(['rand_seed'] + measureCols).sort_index()
	
	fileName = (outFile + '_{}_age_{}_{}').format(timeName, heatAge[0], heatAge[1])
	print(fileName)
	OutputToFile(dfMetric, fileName)


def OutputTimeTablesDraw(
		subfolder, dataPath, measureCols, heatAges, timeName):
	
	cohortEffect = pd.read_csv(subfolder + '/draw_cache/mortHosp_final' + '.csv',
				index_col=[0,1,2], header=[0]).reorder_levels([1, 0, 2])
	
	print('loading DF', timeName)
	start_time = time.time()
	
	dfVac = LoadDf(dataPath, measureCols, timeName, 'vac')
	dfNoVac = LoadDf(dataPath, measureCols, timeName, 'noVac')
	
	dfVac.columns = dfVac.columns.droplevel('run')
	dfNoVac.columns = dfNoVac.columns.droplevel('run')
	
	elapsed_time = time.time() - start_time
	print('elapsed_time {}'.format(elapsed_time))
	start_time = time.time()
	print('reoder levels and transpose', timeName)
	
	dfVac = dfVac.reorder_levels(['rand_seed'] + [timeName] + measureCols, axis=1).sort_index(axis=1)
	dfNoVac = dfNoVac.reorder_levels(['rand_seed'] + [timeName] + measureCols, axis=1).sort_index(axis=1)
	#print(dfVac)
	#print(dfNoVac)
	
	# unstack is 20x faster than stack here.
	dfVac = dfVac.transpose().unstack('rand_seed').transpose()
	dfNoVac = dfNoVac.transpose().unstack('rand_seed').transpose()
	
	elapsed_time = time.time() - start_time
	print('elapsed_time {}'.format(elapsed_time))
	start_time = time.time()
	print('mapping draws', timeName)
	
	# Map draw to random seeds
	drawToSeed = { i:k for i,k in enumerate(list(dfVac.index.unique(level='rand_seed')))}
	index = cohortEffect.index.to_frame()
	index['rand_seed'] = index['draw'].replace(drawToSeed)
	index = index.drop(columns=['draw'])
	cohortEffect.index = pd.MultiIndex.from_frame(index)
	cohortEffect = cohortEffect.sort_index(axis=0)
	
	elapsed_time = time.time() - start_time
	print('elapsed_time {}'.format(elapsed_time))
	start_time = time.time()
	print('Aggregating', timeName)
	
	for heatAge in heatAges:
		for metric in ['infect', 'icu', 'hospital', 'deaths']:
			inName = nameMap.get(metric) if metric in nameMap else metric
			AggregateAgeAndVacDraw(
				dfVac, dfNoVac, cohortEffect, timeName, heatAge,
				subfolder + '/Mort_out/' + metric,
				inName, measureCols)
			AggregateAgeAndVacDraw(
				dfVac, dfNoVac, cohortEffect, timeName, heatAge,
				subfolder + '/Mort_out/' + metric + '_vac',
				inName, measureCols, vacOnly=True)
			AggregateAgeAndVacDraw(
				dfVac, dfNoVac, cohortEffect, timeName, heatAge,
				subfolder + '/Mort_out/' + metric + '_noVac',
				inName, measureCols, noVacOnly=True)


def ApplyCohortEffectsUncertainty(subfolder, measureCols, heatAges, doTenday=False):
	print('ApplyCohortEffects yearlyAgg')
	OutputTimeTablesDraw(subfolder, subfolder + '/Mort_process/', measureCols, heatAges, 'yearlyAgg')
	if doTenday:
		OutputTimeTablesDraw(subfolder, subfolder + '/Mort_process/', measureCols, 'tendayAgg')
	OutputTimeTablesDraw(subfolder, subfolder + '/Mort_process/', measureCols, heatAges, 'weeklyAgg')


############### Draw ###############

def LoadDfDrawRawFile(subfolder, drawCount=100):
	df = pd.read_csv(
		subfolder + '/other_input/death_and_hospital_draws' + '.csv',
		header=[0])
	df = df.rename(columns={
		'age_start' : 'age',
		'deathPerInfect' : 'mort',
		'icuPerInfect' : 'icu',
		'hospitalPerInfect' : 'hosp',
		'draw_' : 'draw',
	})
	df['draw'] = df['draw'] - 1
	df = df[df['draw'] >= 0]
	df = df.set_index(['draw', 'age', 'sex'])
	df = df.groupby(level=['draw', 'age'], axis=0).mean()
	
	return df.astype(float)


def MetricDraw(df, metric):
	#odNumber = stats.norm.ppf(df['seed'], loc=0.693147181, scale=0.14677019)
	df[metric] = stats.norm.ppf(df['seed'], loc=df[metric + '_m'], scale=df[metric + '_se'])
	df[metric] = 1 - 1/(1 + np.exp(df[metric]))
	return df


def GenerateDfFromParams(subfolder, drawCount=100):
	dfParams = pd.read_csv(
		subfolder + '/other_input/draw_params' + '.csv',
		header=[0])
	
	dfOut = pd.DataFrame({
		'draw' : list(range(drawCount)),
		'seed' : np.random.rand(drawCount)
	})
	df = util.CrossDf(dfOut, dfParams)
	df = df.set_index(['draw', 'age'])
	
	df = MetricDraw(df, 'hosp')
	df = MetricDraw(df, 'icu')
	df = MetricDraw(df, 'mort')
	
	return df


def LoadDfDraw(subfolder, drawCount=100, padMult=20, useRawFile=False):
	if useRawFile:
		df = LoadDfDrawRawFile(subfolder, drawCount=drawCount)
	else:
		df = GenerateDfFromParams(subfolder, drawCount=drawCount)
	
	df = df[['hosp', 'icu', 'mort']]
	
	df = CrossIndex(df, pd.DataFrame({'vaccine' : [0, 1]}))
	df = CrossIndex(df, pd.DataFrame({'drawPad' : [i*drawCount for i in range(padMult)]}))
	index = df.index.to_frame()
	index['draw'] = index['drawPad'] + index['draw']
	index = index.drop(columns=['drawPad'])
	df.index = pd.MultiIndex.from_frame(index)
	
	return df


def LoadDfDrawMult(subfolder, drawCount=100, padMult=20):
	df = pd.read_csv(subfolder + '/other_input/death_and_hospital_mult' + '.csv',
				header=[0])
	df = df.rename(columns={
		'age_start' : 'age',
		'deathPerInfect' : 'mort',
		'icuPerInfect' : 'icu',
		'hospitalPerInfect' : 'hosp',
	})
	df = df[df['sex'] == 'female']
	df = df.drop(columns=['sex'])
	df = df.set_index(['vaccine', 'age'])
	df = df[['hosp', 'icu', 'mort']]
	df = CrossIndex(df, pd.DataFrame({'draw' : list(range(drawCount))}))
	
	df_beta = pd.read_csv(subfolder + '/other_input/vaccine_lookup' + '.csv',
				header=[0])
	toDraw = list(df_beta['metric'])
	df_beta = df_beta.set_index(['metric'])
	
	distParams = {k : (df_beta.loc[k, 'alpha'], df_beta.loc[k, 'beta']) for k in toDraw}
	
	np.random.seed(21845)
	for i in range(drawCount):
		df.loc[i, :] = df.loc[i, :].replace({
			k : np.random.beta(
				distParams.get(k)[0], distParams.get(k)[1]
			) for k in toDraw
		}).values
	
	# HAX ALERT: Duplicate because the above loop takes too long at 10000 draws.
	df = CrossIndex(df, pd.DataFrame({'drawPad' : [i*drawCount for i in range(padMult)]}))
	index = df.index.to_frame()
	index['draw'] = index['drawPad'] + index['draw']
	index = index.drop(columns=['drawPad'])
	df.index = pd.MultiIndex.from_frame(index)
	
	return df.astype(float)


def DoDraws(subfolder, measureCols, **kwargs):
	df_draw = LoadDfDraw(subfolder, **kwargs)
	df_mult = LoadDfDrawMult(subfolder, **kwargs)
	
	OutputToFile(df_draw, subfolder + '/draw_cache/' + 'mortHosp_draw')
	OutputToFile(df_mult, subfolder + '/draw_cache/' + 'mortHosp_mult')
	df_draw = df_draw * df_mult
	OutputToFile(df_draw, subfolder + '/draw_cache/' + 'mortHosp_final')


############### Age Heatmaps ###############

def LoadHeatmapInputDf(
		subfolder, measureCols, heatStruct, heatAge, timeName, metric,
		start, end, describe=False, hasRunCol=False, divide=False, doSum=True):
	
	fileIn = '{}_{}_age_{}_{}'.format(metric, timeName, heatAge[0], heatAge[1])
	df = pd.read_csv(
		subfolder + '/Mort_out/' + fileIn + '.csv', 
		index_col=list(range((2 if hasRunCol else 1) + len(measureCols))),
		header=list(range(1)))
	
	df = df[[str(x) for x in range(math.floor(start), math.ceil(end))]]
	
	if divide:
		df = df / divide
	
	# Take a fraction of the metric in fractional weeks.
	if math.floor(start) < start:
		first = str(math.floor(start))
		df[first] = df[first] * (1 - start + math.floor(start))
	if math.ceil(end) > end:
		last = str(math.ceil(end - 1))
		df[last] = df[last] * (1 - math.ceil(end) + end)
	
	if doSum:
		df = df.sum(axis=1)
	return df


def DoHeatmapsDrawRangeHeatAge(
		subfolder, measureCols, heatStruct, heatAge, timeName, metric,
		start, end, describe=False, hasRunCol=False, divide=False, rateDivide=False):
	
	prefixName = '{}_{}_from_{}_to_{}_age_{}_{}'.format(
		timeName,metric,
		util.DecimalLimit(start, 4),util.DecimalLimit(end, 4),
		heatAge[0], heatAge[1])
	
	if divide:
		prefixName = prefixName + '_daily'
	else:
		prefixName = prefixName + '_total'
	
	df = LoadHeatmapInputDf(
		subfolder, measureCols, heatStruct, heatAge, timeName, metric,
		start, end, describe=describe, hasRunCol=hasRunCol,
		divide=divide)
	
	if rateDivide:
		prefixName = prefixName + '_divide_' + rateDivide
		dfDivide = LoadHeatmapInputDf(
			subfolder, measureCols, heatStruct, heatAge, timeName, rateDivide,
			start, end, describe=describe, hasRunCol=hasRunCol,
			divide=divide)
		
		df = df.div(dfDivide)
	
	if util.HasDuplicateIndex(df):
		print('Warning: Duplicate index')
		df = df[~df.index.duplicated()]
	
	util.MakeDescribedHeatmapSet(
		subfolder + '/Heatmaps/', df,
		heatStruct, prefixName, describe=describe)

def DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, metric,
		start, end, **kwargs):
	
	for heatAge in heatAges:
		DoHeatmapsDrawRangeHeatAge(
			subfolder, measureCols, heatStruct, heatAge, timeName, metric,
			start, end, **kwargs)


############### ICU ###############

def DoIcuHeatmaps(
		subfolder, measureCols, heatStruct, start, end,
		icuStart, icuEnd, icuCapacity, describe):
	
	prefixName = 'icu_delay_{}_to_{}_cap_{}_from_{}_to_{}'.format(
		util.DecimalLimit(icuStart*7, 2),util.DecimalLimit(icuEnd*7, 2), icuCapacity,
		util.DecimalLimit(start, 2),util.DecimalLimit(end, 2))
	
	traceName = 'icu_delay_{}_to_{}_from_{}_to_{}'.format(
		util.DecimalLimit(icuStart*7, 2),util.DecimalLimit(icuEnd*7, 2),
		util.DecimalLimit(start, 4),util.DecimalLimit(end, 4))
	
	dfIcu = LoadHeatmapInputDf(
		subfolder, measureCols, heatStruct, [0, 110], 'weeklyAgg', 'icu',
		0, end, describe=describe, doSum=False)
	
	df = dfIcu.copy()
	
	# Add the ICU intake from the previous <icuWeeks> weeks
	df.columns = list(range(0, math.ceil(end)))
	df = df.applymap(lambda x: 0)
	
	if icuStart != math.ceil(icuStart):
		window = math.floor(icuStart)
		dfAdd = dfIcu.copy()
		dfAdd.columns = list(range(window, math.ceil(end + window)))
		dfAdd = dfAdd[list(range(window, math.ceil(end)))]
		dfAdd = dfAdd * (math.ceil(icuStart) - icuStart)
		df = df.add(dfAdd, fill_value=0)
	
	if icuEnd != math.floor(icuEnd):
		window = math.floor(icuEnd)
		dfAdd = dfIcu.copy()
		dfAdd.columns = list(range(window, math.ceil(end + window)))
		dfAdd = dfAdd[list(range(window, math.ceil(end)))]
		dfAdd = dfAdd * (icuEnd - math.floor(icuEnd))
		df = df.add(dfAdd, fill_value=0)
	
	for i in range(math.ceil(icuStart), math.floor(icuEnd)):
		dfAdd = dfIcu.copy()
		dfAdd.columns = list(range(i, math.ceil(end + i)))
		dfAdd = dfAdd[list(range(i, math.ceil(end)))]
		df = df.add(dfAdd, fill_value=0)
	
	df = df[list(range(math.floor(start), math.ceil(end)))]
	OutputToFile(df, subfolder + '/Traces/' + traceName)
	
	df = df.applymap(lambda x: 0 if x < icuCapacity else 1)
	df = df.mean(axis=1)
	
	if util.HasDuplicateIndex(df):
		print('Warning: Duplicate index')
		df = df[~df.index.duplicated()]
	
	util.MakeDescribedHeatmapSet(
		subfolder + '/Heatmaps/', df,
		heatStruct, prefixName, describe=describe)


############### Load Heatmaps From Traces ###############

def LoadHeatmapTraceInputDf(
		subfolder, measureCols, heatStruct, timeName, metric,
		start, end, describe=False, hasRunCol=False, divide=False, doSum=True):
	
	fileIn = 'processed_{}_{}'.format(metric, timeName)
	df = pd.read_csv(
		subfolder + '/Traces/' + fileIn + '.csv', 
		index_col=list(range((2 if hasRunCol else 1) + len(measureCols))),
		header=list(range(1)))
	
	df = df[[str(float(x)) for x in range(math.floor(start), math.ceil(end))]]
	
	if divide:
		df = df / divide
	
	# Take a fraction of the metric in fractional weeks.
	if math.floor(start) < start:
		first = str(float(math.floor(start)))
		df[first] = df[first] * (1 - start + math.floor(start))
	if math.ceil(end) > end:
		last = str(float(math.ceil(end - 1)))
		df[last] = df[last] * (1 - math.ceil(end) + end)
	
	if doSum:
		df = df.sum(axis=1)
		
	return df


def DoHeatmapsRangeFromTrace(
		subfolder, measureCols, heatStruct, timeName, metric, aggSize,
		start, end, describe):
	
	prefixName = '{}_{}_from_{}_to_{}_age_{}_{}'.format(
		timeName, metric,
		util.DecimalLimit(start, 4),util.DecimalLimit(end, 4),
		0, 110)
	
	df = LoadHeatmapTraceInputDf(subfolder, measureCols, heatStruct, timeName, metric, start, end, hasRunCol=True)
	
	util.MakeDescribedHeatmapSet(
		subfolder + '/Heatmaps/', df,
		heatStruct, prefixName, describe=describe)


def DoTraceHeatmaps(
		subfolder, measureCols, heatStruct, timeName, aggSize,
		start, end, describe):
	
	DoHeatmapsRangeFromTrace(subfolder, measureCols, heatStruct, timeName,  'case7', aggSize, start, end, describe)


############### API ###############

def PreProcessMortHosp(subfolder, measureCols):
	ProcessInfectionCohorts(subfolder, measureCols)


def DrawMortHospDistributions(subfolder, measureCols, **kwargs):
	DoDraws(subfolder, measureCols, **kwargs)


def FinaliseMortHosp(subfolder, measureCols, heatAges, doTenday=False):
	ApplyCohortEffectsUncertainty(subfolder, measureCols, heatAges, doTenday=doTenday)


def MakeIcuHeatmaps(
		subfolder, measureCols, heatStruct, start, window,
		icuStart=10/7, icuEnd=19/7, icuCapacity=600, describe=True):
	DoIcuHeatmaps(
		subfolder, measureCols, heatStruct, start, start + window,
		icuStart, icuEnd, icuCapacity, describe)


def MakeCaseHeatmaps(subfolder, measureCols, heatAges, heatStruct, timeName, start, window, describe=True):
	end = start + window
	DoHeatmapsDrawRange(subfolder + '/Trace/', measureCols, heatStruct, 'processed_case7_' + timeName, start, end, describe=describe, hasRunCol=True)


def MakeMortHospHeatmapRange(
		subfolder, measureCols, heatAges, heatStruct, timeName, start, window,
		describe=True, doExtras=True, doIfr=True, doVacSplit=False,
		deathLag=0, aggSize=7):
	end = start + window
	totalDays = aggSize * window
	
	DoTraceHeatmaps(subfolder, measureCols, heatStruct, timeName, aggSize, start, end, describe=describe)
	
	DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, 'icu_vac',
		start, end, describe=describe)
	DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, 'infect_vac',
		start, end, describe=describe)
	DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, 'hospital_vac',
			start, end, describe=describe)
	DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, 'deaths_vac',
		max(0, start - deathLag), end - deathLag, describe=describe)
	DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, 'infect_noVac',
		start, end, describe=describe)
	DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, 'icu_noVac',
		start, end, describe=describe)
	DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, 'hospital_noVac',
			start, end, describe=describe)
	DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, 'deaths_noVac',
		max(0, start - deathLag), end - deathLag, describe=describe)

	DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, 'deaths',
		max(0, start - deathLag), end - deathLag, describe=describe)
	DoHeatmapsDrawRange(
		subfolder, measureCols, heatStruct, heatAges, timeName, 'infect',
		start, end, describe=describe)
	
	if doIfr:
		DoHeatmapsDrawRange(
			subfolder, measureCols, heatStruct, heatAges, timeName, 'deaths',
			max(0, start - deathLag), end - deathLag, describe=describe, rateDivide='infect')
	
	if doVacSplit:
		DoHeatmapsDrawRange(
			subfolder, measureCols, heatStruct, heatAges, timeName, 'infect_vac',
			start, end, describe=describe, rateDivide='infect')
		DoHeatmapsDrawRange(
			subfolder, measureCols, heatStruct, heatAges, timeName, 'infect_noVac',
			start, end, describe=describe, rateDivide='infect')
		DoHeatmapsDrawRange(
			subfolder, measureCols, heatStruct, heatAges, timeName, 'infect_vac',
			start, end, describe=describe, rateDivide='infect_noVac')
	
	if doExtras:
		DoHeatmapsDrawRange(
			subfolder, measureCols, heatStruct, heatAges, timeName, 'infect',
			start, end, divide=totalDays, describe=describe)
		DoHeatmapsDrawRange(
			subfolder, measureCols, heatStruct, heatAges, timeName, 'hospital',
			start, end, describe=describe)
		DoHeatmapsDrawRange(
			subfolder, measureCols, heatStruct, heatAges, timeName, 'icu',
			start, end, describe=describe)

