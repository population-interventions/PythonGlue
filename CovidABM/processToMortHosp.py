# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 10:22:33 2021

@author: wilsonte
"""

import math
import pandas as pd
import numpy as np
from tqdm import tqdm
import pathlib
import time
import os

from utilities import AddFiles
from utilities import ToHeatmap, CrossIndex
from utilities import OutputToFile, GetCohortData, ListRemove
import utilities as util


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
	

def AggregateAgeAndVac(dfVac, dfNoVac, cohortEffect, timeName, metric):
	dfMultVac = MultiplyByCohortEffect(dfVac, cohortEffect.loc[1][metric])
	dfMultNoVac = MultiplyByCohortEffect(dfNoVac, cohortEffect.loc[0][metric])
	
	dfMetric = dfMultVac + dfMultNoVac
	dfMetric = dfMetric.transpose()
	dfMetric = dfMetric.unstack(level=[timeName])
	
	dfMetric = dfMetric.groupby(level=[timeName], axis=1).sum()
	return dfMetric


def OutputTimeTables(subfolder, dataPath, measureCols, timeName):
	cohortEffect = GetEffectsData(subfolder + '/other_input/death_and_hospital')
	
	print('loading DF', timeName)
	dfVac = LoadDf(dataPath, measureCols, timeName, 'vac')
	dfNoVac = LoadDf(dataPath, measureCols, timeName, 'noVac')
	
	print('Aggregating', timeName)
	dfDeaths = AggregateAgeAndVac(dfVac, dfNoVac, cohortEffect, timeName, 'mort')
	dfHospital = AggregateAgeAndVac(dfVac, dfNoVac, cohortEffect, timeName, 'hosp')
	
	OutputToFile(dfDeaths, subfolder + '/Mort_out/deaths_' + timeName)
	OutputToFile(dfHospital, subfolder + '/Mort_out/hospital_' + timeName)
		

def ApplyCohortEffects(subfolder, measureCols):
	print('ApplyCohortEffects yearlyAgg')
	OutputTimeTables(subfolder, subfolder + '/Mort_process/', measureCols, 'yearlyAgg')
	print('ApplyCohortEffects weeklyAgg')
	OutputTimeTables(subfolder, subfolder + '/Mort_process/', measureCols, 'weeklyAgg')


############### Multiplication Uncertainty ###############

def AggregateAgeAndVacDraw(dfVac, dfNoVac, cohortEffect, timeName, metric, measureCols):
	dfVac = dfVac.mul(cohortEffect.loc[1][metric], axis=0)
	dfNoVac = dfNoVac.mul(cohortEffect.loc[1][metric], axis=0)
	
	dfMetric = dfVac + dfNoVac
	dfMetric = dfMetric.transpose()
	dfMetric = dfMetric.stack(level=['rand_seed'])
	dfMetric = dfMetric.unstack(level=[timeName])
	dfMetric = dfMetric.groupby(level=[timeName], axis=1).sum()
	dfMetric = dfMetric.reorder_levels(['rand_seed'] + measureCols).sort_index()
	return dfMetric


def OutputTimeTablesDraw(subfolder, dataPath, measureCols, timeName):
	cohortEffect = pd.read_csv(subfolder + '/draw_cache/mortHosp_final' + '.csv',
				index_col=[0,1,2], header=[0]).reorder_levels([1, 0, 2])
	
	print('loading DF', timeName)
	dfVac = LoadDf(dataPath, measureCols, timeName, 'vac')
	dfNoVac = LoadDf(dataPath, measureCols, timeName, 'noVac')
	
	dfVac.columns = dfVac.columns.droplevel('run')
	dfNoVac.columns = dfNoVac.columns.droplevel('run')
	
	dfVac = dfVac.stack('rand_seed')
	dfNoVac = dfNoVac.stack('rand_seed')
	
	# Map draw to random seeds
	drawToSeed = { i:k for i,k in enumerate(list(dfVac.index.unique(level='rand_seed')))}
	index = cohortEffect.index.to_frame()
	index['rand_seed'] = index['draw'].replace(drawToSeed)
	index = index.drop(columns=['draw'])
	cohortEffect.index = pd.MultiIndex.from_frame(index)
	cohortEffect = cohortEffect.sort_index(axis=0)
	
	print('Aggregating', timeName)
	dfDeaths = AggregateAgeAndVacDraw(dfVac, dfNoVac, cohortEffect, timeName, 'mort', measureCols)
	dfHospital = AggregateAgeAndVacDraw(dfVac, dfNoVac, cohortEffect, timeName, 'hosp', measureCols)
	
	OutputToFile(dfDeaths, subfolder + '/Mort_out/deaths_draw_' + timeName)
	OutputToFile(dfHospital, subfolder + '/Mort_out/hospital_draw_' + timeName)
	
	
def ApplyCohortEffectsUncertainty(subfolder, measureCols):
	print('ApplyCohortEffects yearlyAgg')
	OutputTimeTablesDraw(subfolder, subfolder + '/Mort_process/', measureCols, 'yearlyAgg')


############### Draw ###############

def LoadDfDraw(subfolder, drawCount=100, padMult=20):
	df = pd.read_csv(subfolder + '/other_input/death_and_hospital_draws' + '.csv',
				header=[0])
	df = df.rename(columns={
		'age_start' : 'age',
		'deathPerInfect' : 'mort',
		'hospitalPerInfect' : 'hosp',
		'draw_' : 'draw',
	})
	df['draw'] = df['draw'] - 1
	df = df[df['draw'] >= 0]
	df = df.set_index(['draw', 'age', 'sex'])
	df = df.groupby(level=['draw', 'age'], axis=0).mean()
	df = CrossIndex(df, pd.DataFrame({'vaccine' : [0, 1]}))
	
	# HAX ALERT: Duplicate externally sourced draws to match current data.
	df = CrossIndex(df, pd.DataFrame({'drawPad' : [i*drawCount for i in range(padMult)]}))
	index = df.index.to_frame()
	index['draw'] = index['drawPad'] + index['draw']
	index = index.drop(columns=['drawPad'])
	df.index = pd.MultiIndex.from_frame(index)
	
	return df.astype(float)


def LoadDfDrawMult(subfolder, drawCount=100, padMult=20):

	df = pd.read_csv(subfolder + '/other_input/death_and_hospital_mult' + '.csv',
				header=[0])
	df = df.rename(columns={
		'age_start' : 'age',
		'deathPerInfect' : 'mort',
		'hospitalPerInfect' : 'hosp',
	})
	df = df[df['sex'] == 'female']
	df = df.drop(columns=['sex'])
	df = df.set_index(['vaccine', 'age'])
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


############### Heatmaps ###############

def DoHeatmaps(subfolder, measureCols, heatmapStructure, metric, years=1, describe=False):
	df = pd.read_csv(subfolder + '/Mort_out/' + metric + '_yearlyAgg' + '.csv', 
					index_col=list(range(2 + len(measureCols))),
					header=list(range(1)))
	
	if describe:
		print('Describe {}'.format(metric))
		name =  metric + '_full_' + 'describe'
		df_describe = df.copy()
		index = heatmapStructure.get('index_rows') + heatmapStructure.get('index_cols')
		df_describe = df_describe.unstack(index)
		df_describe = df_describe.describe(percentiles=[0.05,0.25,0.75,0.95])
		OutputToFile(df_describe, subfolder + '/Mort_heatmaps/' + name, head=False)
		
	df = df.groupby(level=measureCols, axis=0).mean()
	df_full = ToHeatmap(df.sum(axis=1).reset_index(), heatmapStructure)
	df_year1 = ToHeatmap(df['0'].reset_index(), heatmapStructure)
	if years == 2:
		df_year2 = ToHeatmap(df['1'].reset_index(), heatmapStructure)
	
	OutputToFile(df_full, subfolder + '/Mort_heatmaps/' + metric + '_total_full', head=False)
	if years == 2:
		OutputToFile(df_year1, subfolder + '/Mort_heatmaps/' + metric + '_total_0_to_52', head=False)
		OutputToFile(df_year2, subfolder + '/Mort_heatmaps/' + metric + '_total_52_to_104', head=False)


def DoHeatmapsDraw(subfolder, measureCols, heatmapStructure, metric, years=1, describe=False):
	df = pd.read_csv(subfolder + '/Mort_out/' + metric + '_yearlyAgg' + '.csv', 
					index_col=list(range(1 + len(measureCols))),
					header=list(range(1)))
	
	percentList = [0.05, 0.5, 0.95]
	yearList = ['full']
	if years > 1:
		yearList += [str(i) for i in range(years)]
	
	percMap = {
		0.05: 'percentile_005',
		0.95 : 'percentile_095',
		0.5 : 'percentile_050',
	}
	nameMap = {
		'0': '0_to_52',
		'1': '52_to_104',
		'full' : 'full'
	}
	
	df['full'] = df['0']
	if years == 2:
		df['full'] = df['0'] + df['1']

	if describe:
		for year in yearList:
			name =  metric + '_total_' + nameMap.get(year) + '_' + 'describe'
			print('Describe {} draws'.format(metric))
			df_describe = df.loc[:, year].copy()
			index = heatmapStructure.get('index_rows') + heatmapStructure.get('index_cols')
			df_describe = df_describe.unstack(index)
			df_describe = df_describe.describe(percentiles=[0.05,0.25,0.75,0.95])
			OutputToFile(df_describe, subfolder + '/Mort_heatmaps/' + name, head=False)
		
	dfMean = df.copy()
	dfMean = dfMean.groupby(level=measureCols, axis=0).mean()
	
	df = df.groupby(level=measureCols, axis=0).quantile(percentList)
	df.index.names = measureCols + ['percentile']
	df = df.reorder_levels(['percentile'] + measureCols).sort_index()

	for year in yearList:
		dfHeat = ToHeatmap(dfMean.loc[:, year].reset_index(), heatmapStructure)
		name =  metric + '_total_' + nameMap.get(year) + '_' + 'mean'
		print('Output heatmap {}'.format(name))
		OutputToFile(dfHeat, subfolder + '/Mort_heatmaps/' + name, head=False)
		
	for pc in percentList:
		for year in yearList:
			dfHeat = ToHeatmap(df.loc[pc, year].reset_index(), heatmapStructure)
			name =  metric + '_total_' + nameMap.get(year) + '_' + percMap.get(pc)
			print('Output heatmap {}'.format(name))
			OutputToFile(dfHeat, subfolder + '/Mort_heatmaps/' + name, head=False)


############### API ###############

def PreProcessMortHosp(subfolder, measureCols):
	ProcessInfectionCohorts(subfolder, measureCols)
	
	
def DrawMortHospDistributions(subfolder, measureCols, **kwargs):
	DoDraws(subfolder, measureCols, **kwargs)
	

def FinaliseMortHosp(subfolder, measureCols):
	ApplyCohortEffects(subfolder, measureCols)
	ApplyCohortEffectsUncertainty(subfolder, measureCols)
	
 
def MakeMortHospHeatmaps(subfolder, measureCols, heatmapStructure, years=1, describe=False):
	DoHeatmaps(subfolder, measureCols, heatmapStructure, 'deaths', years=years, describe=describe)
	DoHeatmaps(subfolder, measureCols, heatmapStructure, 'hospital', years=years, describe=describe)
	DoHeatmapsDraw(subfolder, measureCols, heatmapStructure, 'deaths_draw', years=years, describe=describe)
	DoHeatmapsDraw(subfolder, measureCols, heatmapStructure, 'hospital_draw', years=years, describe=describe)

