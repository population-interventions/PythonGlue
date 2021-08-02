import math
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import os
import re

from utilities import OutputToFile, GetCohortData

############### Shared ###############

def Output(df, path):
	index = df.index.to_frame(index=False)
	index = index.drop(columns=['run'])
	df.index = pd.MultiIndex.from_frame(index)
	df = df.rename('value')
	
	# Consider the following as a nicer replacement:
	#"for name, subDf in df.groupby(level=0):"
	for value in index.rand_seed.unique():
		rdf = df[df.index.isin([value], level=0)]
		rdf = rdf.reset_index()
		rdf = rdf.drop(columns='rand_seed')
		OutputToFile(rdf, path + '_' + str(value), index=False)


def LoadColumn(path, inName, indexCols):
	return pd.read_csv(path + '_' + inName + '.csv',
				header=[0],
				index_col=list(range(indexCols)))


def CombineDrawColumnsAndFindDraw0(prefix, append, index_size=8):
	fileList = os.listdir(prefix)
	fileList = [x for x in fileList if '_head' not in x]
	nameList = list(set(list(map(
		lambda x: int(x[re.search(r'\d', x).start():x.find('.')]), fileList))))
	nameList.sort()
	
	draw_prefix = prefix + append
	df = None
	for n, value in tqdm(enumerate(nameList), total=len(nameList)):
		if n == 0:
			df = LoadColumn(draw_prefix, str(value), index_size)
			df = df.rename(columns={'value' : 'draw_1'})
		else:
			df['draw_' + str(n + 1)] = LoadColumn(draw_prefix, str(value), index_size)['value']

	df['draw_0'] = df.mean(axis=1)
	return df    


############### Infection Step 1 - Make two csvs for each random seed ###############

def ProcessInfectChunk(df, chortDf, outputPrefix, months):
	df.columns = df.columns.set_levels(df.columns.levels[1].astype(int), level=1)
	df.columns = df.columns.set_levels(df.columns.levels[2].astype(int), level=2)
	df = df.sort_values(['cohort', 'day'], axis=1)
	
	col_index = df.columns.to_frame()
	col_index = col_index.reset_index(drop=True)
	col_index['month'] = np.floor(col_index['day']*12/365).astype(int)
	col_index = pd.merge(
		col_index, chortDf,
		on='cohort',
		how='left',
		sort=False)
	col_index = col_index.drop(columns=['atsi', 'morbid'])
	df.columns = pd.MultiIndex.from_frame(col_index)
	
	df = df.groupby(level=[4, 3], axis=1).sum()
	
	# In the ABM age range 15 represents ages 10-17 while age range 25 is
	# ages 18-30. First redestribute these cohorts so they align with 10 year
	# increments.
	df[15], df[25] = df[15] + df[25]/5, df[25]*4/5

	# 60-69 year olds are already split.
	df = df.rename(columns={
		62 : 62.5,
		67 : 67.5,
	})

	# Then split the 10 year cohorts in half.
	ageCols = [i*10 + 5 for i in range(9)]
	ageCols.remove(65)
	for age in ageCols:
		for j in range(months):
			# TODO, vectorise?
			df[age - 2.5, j] = df[age, j]/2
			df[age + 2.5, j] = df[age, j]/2
	
	# Add extra cohorts missing from ABM
	for j in range(months):
		df[92.5, j] = 0
		df[97.5, j] = 0
		df[102.5, j] = 0
		df[107.5, j] = 0
	
	df = df.drop(columns=ageCols, level=0)
	df = df.stack(level=[0,1])
	Output(df, outputPrefix)
	

def ProcessInfectCohorts(measureCols, filename, cohortFile, outputPrefix, months):
	cohortData = GetCohortData(cohortFile)
	chunksize = 4 ** 7
	
	for chunk in tqdm(
			pd.read_csv(filename + '.csv', 
				index_col=list(range(2 + len(measureCols))),
				header=list(range(3)),
				dtype={'day' : int, 'cohort' : int},
				chunksize=chunksize),
			total=4):
		ProcessInfectChunk(chunk, cohortData, outputPrefix, months)


############### Infection Step 2 ###############


def GetEffectsData(file):
	df = pd.read_csv(file + '.csv',
				header=[0])
	df = df.set_index(['vaccine', 'age_start', 'sex'])
	return df


def ProcessInfectionTable(df, months=12):
	index = df.index.to_frame()
	index['year_start'] = (index['month'])/12
	index['year_end']   = (index['month'] + 1)/12
	index['age_start']  = index['age'] - 2.5
	index['age_end']    = index['age'] + 2.5
	index = index.drop(columns=['age', 'month'])
	df.index = pd.MultiIndex.from_frame(index)
	
	enddf = df[df.index.isin([(months - 0.5)/12], level=7)]
	enddf = enddf*0
	index = enddf.index.to_frame()
	index['year_start'] = index['year_end']
	index['year_end']   = 120
	enddf.index = pd.MultiIndex.from_frame(index)
	df = df.append(enddf)
	
	df = pd.concat([df, df], axis=1, keys=('male','female'))/2
	df.columns = df.columns.set_names('sex', level=[0])
	df = df.stack(level=[0])
	return df


def MultiplyByCohortEffect(measureCols, df, multDf):
	df = df.mul(multDf, axis=0)
	df.index = df.index.reorder_levels(order=(measureCols + [
		'sex', 'age_start', 'age_end', 'year_start', 'year_end']))
	return df
	

def AddAndFinalisePmsltInputs(measureCols, subfolder, path, output, months=12):
	cohortEffect = GetEffectsData(subfolder + '/other_input/chort_effects')
	
	df_infect_vac = CombineDrawColumnsAndFindDraw0(path + 'infect_results/', 'infect_vac',
												   index_size=(2 + len(measureCols)))
	df_infect_vac = ProcessInfectionTable(df_infect_vac, months)
	
	df_infect_NoVac = CombineDrawColumnsAndFindDraw0(path + 'infect_results/', 'infect_noVac',
													 index_size=(2 + len(measureCols)))
	df_infect_NoVac = ProcessInfectionTable(df_infect_NoVac, months)
	
	df_mort_vac   = MultiplyByCohortEffect(measureCols, df_infect_vac, cohortEffect.loc[1]['mort'])
	df_mort_noVac = MultiplyByCohortEffect(measureCols, df_infect_NoVac, cohortEffect.loc[0]['mort'])
	df_morb_vac   = MultiplyByCohortEffect(measureCols, df_infect_vac, cohortEffect.loc[1]['morb'])
	df_morb_noVac = MultiplyByCohortEffect(measureCols, df_infect_NoVac, cohortEffect.loc[0]['morb'])
	df_expd_vac   = MultiplyByCohortEffect(measureCols, df_infect_vac, cohortEffect.loc[1]['expenditure'])
	df_expd_noVac = MultiplyByCohortEffect(measureCols, df_infect_NoVac, cohortEffect.loc[0]['expenditure'])
	
	OutputToFile(df_mort_vac + df_mort_noVac, output + '/acute_disease.covid.mortality')
	OutputToFile(df_morb_vac + df_morb_noVac, output + '/acute_disease.covid.morbidity')
	OutputToFile(df_expd_vac + df_expd_noVac, output + '/acute_disease.covid.expenditure')


############### Stages Step 1 - Output each random seed to csv ###############     

def ProcessChunkStage(df, outputPrefix):
	df.columns = df.columns.set_levels(df.columns.levels[1].astype(int), level=1)
	df.columns = df.columns.set_levels(df.columns.levels[2].astype(int), level=2)
	
	df.columns = df.columns.droplevel([0, 2])
	
	col_index = df.columns.to_frame()
	col_index = col_index.reset_index(drop=True)
	col_index['month'] = np.floor(col_index['day']*12/365).astype(int)
	df.columns = pd.MultiIndex.from_frame(col_index)
	
	df = df.apply(lambda c: [1 if x > 2 else 0 for x in c])
	df = df.groupby(level=[1], axis=1).mean()
	
	df = df.stack(level=[0])
	Output(df, outputPrefix)


def ProcessStageCohorts(measureCols, filename, outputPrefix):
	chunksize = 4 ** 7
	
	for chunk in tqdm(
			pd.read_csv(filename + '.csv', 
				index_col=list(range(2 + len(measureCols))),
				header=list(range(3)),
				dtype={'day' : int, 'cohort' : int},
				chunksize=chunksize),
			total=4):
		ProcessChunkStage(chunk, outputPrefix)


############### Stages Step 2 - Combine and Process ###############

def CombineDrawsStageAndFinalise(measureCols, subfolder, path, output, months=12):
	df = CombineDrawColumnsAndFindDraw0(path, 'stage', index_size=(1 + len(measureCols)))
	
	index = df.index.to_frame()
	index = index[measureCols + ['month']]
	index['year_start'] = (index['month'])/12
	index['year_end']   = (index['month'] + 1)/12
	index = index.drop(columns=['month'])
	df.index = pd.MultiIndex.from_frame(index)

	enddf = df[df.index.isin([(months - 0.5)/12], level=1 + len(measureCols))]
	enddf = enddf*0
	index = enddf.index.to_frame()
	index['year_start'] = index['year_end']
	index['year_end']   = 120
	enddf.index = pd.MultiIndex.from_frame(index)
	df = df.append(enddf)
	
	OutputToFile(df, output + '/lockdown_stage')


############### Aggregates ###############
def OutputAggregate(subfolder, measureCols):
	df = pd.read_csv(
		subfolder + 'acute_disease.covid.morbidity' + '.csv',
		index_col=list(range(6 + len(measureCols))),
		header=[0])
	df = df.groupby(level=[8, 9], axis=0).sum()
	OutputToFile(df, subfolder + 'aggregate')


############### Run Infection Processing ###############

def ProcessInfectionCohorts(subfolder, measureCols, months):
	print('Processing vaccination infection for PMSLT')
	ProcessInfectCohorts(
		measureCols,
		subfolder + '/ABM_process/processed_infectVac',
		subfolder + '/ABM_process/processed_static',
		subfolder + '/PMSLT_process/infect_results/infect_vac',
		months)
	print('Processing non-vaccination infection for PMSLT')
	ProcessInfectCohorts(
		measureCols,
		subfolder + '/ABM_process/processed_infectNoVac',
		subfolder + '/ABM_process/processed_static',
		subfolder + '/PMSLT_process/infect_results/infect_noVac',
		months)
	
def ProcessInfection(subfolder, measureCols, months=12):
	ProcessInfectionCohorts(subfolder, measureCols, months)
	
	print('Finalising infection PMSLT input')
	AddAndFinalisePmsltInputs(
		measureCols, subfolder,
		subfolder + '/PMSLT_process/', subfolder + '/PMSLT_input',
		months=12)

def ProcessStages(subfolder, measureCols, months=12):
	print('Processing stages for PMSLT')
	ProcessStageCohorts(
		measureCols,
		subfolder + '/ABM_process/processed_stage', subfolder + '/PMSLT_process/stage_results/stage')
	print('Finalising stages PMSLT input')
	CombineDrawsStageAndFinalise(
		measureCols, subfolder,
		subfolder + '/PMSLT_process/stage_results/', subfolder + '/PMSLT_input',
		months=12)


def DoProcessingForPMSLT(subfolder, measureCols, months=12):
	ProcessInfection(subfolder, measureCols, months)
	ProcessStages(subfolder, measureCols, months)


def GetAggregates(subfolder, measureCols):
	OutputAggregate(subfolder + '/PMSLT_input/', measureCols)
