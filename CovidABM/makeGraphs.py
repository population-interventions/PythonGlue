
import math
import pandas as pd
import numpy as np

from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

from utilities import OutputToFile
from utilities import ToHeatmap

def MakeFavouriteGraph(dataDir, dataName, measureCols, favParams, median=True, mean=True, si=False):
	processDir = dataDir + '/ABM_process/'
	visualDir = dataDir + '/Graphs/'
	inputFile = processDir + dataName + '_weeklyAgg'
	
	df = pd.read_csv(
		inputFile + '.csv',
		index_col=list(range(2 + len(measureCols))),
		header=list(range(1)))
	
	df = df.drop(columns=['105.0']) # The last week is incomplete)
	df['0.0'] = df['0.0'] / 2.5
	df.index = df.index.droplevel(['run'])
	df = df.reorder_levels([1, 2, 3, 4, 5, 0], axis=0)
	df = df.sort_index()
	
	df = df / 7
	for val in favParams:
		df = df.loc[val] 
	
	df = df.describe(percentiles=[0.05, 0.95])
	
	metrics = []
	if median:
		metrics += ['50%']
	if mean:
		metrics += ['mean']
	if si:
		metrics += ['5%', '95%']
		
	df = df.loc[metrics].transpose()
	
	df.plot()
	

def MakeDailyGraphs(
		dataDir, dataName, measureCols, splitParam,
		median=True, mean=True, si=False, filterIndex=[], days=364):
	processDir = dataDir + '/ABM_process/'
	visualDir = dataDir + '/Graphs/'
	
	df = pd.read_csv(
		processDir + dataName + '_daily' + '.csv',
		index_col=list(range(2 + len(measureCols))),
		header=list(range(1)))
	#OutputToFile(df, visualDir + 'daily_infections')
	
	#df = df.drop(columns=[str(weeks) + '.0']) # The last week is incomplete)
	df.index = df.index.droplevel(['run'])
	df = df.reorder_levels(measureCols + ['rand_seed'], axis=0)
	df = df.sort_index()
	
	for toFilter in filterIndex:
		df = df.xs(toFilter[1], level=toFilter[0])
	plotCols = [x for x in measureCols if x not in [y[0] for y in filterIndex]]
	
	df.columns.name = 'week'
	df = df.drop_duplicates(subset=None, keep='first')
	df = df.unstack(plotCols)
	OutputToFile(df, visualDir + 'focus_data_in')
	
	metrics = []
	if median:
		metrics += ['50%']
	if mean:
		metrics += ['mean']
	if si:
		if si == True:
			si = [0.25, 0.75]
		metrics += ['{:.0f}%'.format(x*100) for x in si]
	else:
		si = [0.25, 0.75]
	
	smallFont = 20
	bigFont = 26
	
	df = df.describe(percentiles=si)
	df = df.loc[metrics].stack(splitParam).transpose()
	df.index = df.index.astype(float)
	df = df.sort_index(axis=0)
	df = df.sort_index(axis=1)
	print(df)
	
	plt.rcParams.update(plt.rcParamsDefault)
	
	figure = df.plot(figsize=(16.1, 10), linewidth=4, fontsize=smallFont)
	plt.grid(which='both')
	figure.set_ylim(0, 500)
	plt.legend(fontsize=bigFont)
	plt.xlabel("Day", fontsize=bigFont)
	plt.ylabel("Daily infections", fontsize=bigFont)
	plt.xticks([x*14 for x in range(math.ceil(days/14))])
	figure.set_xlim(0, 300)
	plt.show()
	#OutputToFile(df, visualDir + dataName + 'fullGraphPlot')


def MakePrettyGraphs(
		dataDir, dataName, measureCols, splitParam,
		median=True, mean=True, si=False, filterIndex=[], timesteps=30):
	processDir = dataDir + '/ABM_process/'
	visualDir = dataDir + '/Graphs/'
	inputFile = processDir + dataName
	
	df = pd.read_csv(
		inputFile + '.csv',
		index_col=list(range(2 + len(measureCols))),
		header=list(range(1)))
	
	#df = df.drop(columns=[str(weeks) + '.0']) # The last week is incomplete)
	df.index = df.index.droplevel(['run'])
	df = df.reorder_levels(measureCols + ['rand_seed'], axis=0)
	df = df.sort_index()
	
	df = df
	for toFilter in filterIndex:
		df = df.xs(toFilter[1], level=toFilter[0])
	plotCols = [x for x in measureCols if x not in [y[0] for y in filterIndex]]
	
	df.columns.name = 'time'
	df = df.drop_duplicates(subset=None, keep='first')
	df = df.unstack(plotCols)
	OutputToFile(df, visualDir + 'focus_data_in')
	
	metrics = []
	if median:
		metrics += ['50%']
	if mean:
		metrics += ['mean']
	if si:
		if si == True:
			si = [0.25, 0.75]
		metrics += ['{:.0f}%'.format(x*100) for x in si]
	else:
		si = [0.25, 0.75]
	
	smallFont = 20
	bigFont = 26
	
	df = df.describe(percentiles=si)
	df = df.loc[metrics].stack(splitParam).transpose()
	print(df)
	df.index = df.index.astype(float)
	df = df.sort_index(axis=0)
	df = df.sort_index(axis=1)
	print(df)
	
	plt.rcParams.update(plt.rcParamsDefault)
	
	figure = df.plot(figsize=(16.1, 10), linewidth=4, fontsize=smallFont)
	plt.grid(which='both')
	figure.set_ylim(0, 1000)
	figure.set_xlim(0, timesteps)
	plt.legend(fontsize=bigFont)
	plt.xlabel("Day", fontsize=bigFont)
	plt.ylabel("Median " + dataName, fontsize=bigFont)
	plt.xticks([x*7 for x in range(math.ceil(timesteps/7))])
	plt.show()
	#OutputToFile(df, visualDir + dataName + 'fullGraphPlot')


def MakeMultiSplitGraphs(
		dataDir, dataName, measureCols, splitParams,
		median=True, mean=True, si=False):
	processDir = dataDir + '/ABM_process/'
	visualDir = dataDir + '/Graphs/'
	inputFile = processDir + dataName + '_weeklyAgg'
	
	df = pd.read_csv(
		inputFile + '.csv',
		index_col=list(range(3 + len(measureCols))),
		header=list(range(1)))
	
	print(df)
	df = df.drop(columns=['0.0', '105.0']) # The last week is incomplete)
	df.index = df.index.droplevel(['run'])
	df = df.reorder_levels([1, 3, 4, 5, 6, 7, 8, 0, 2], axis=0)
	df = df.sort_index()
	
	df = df / 7
	df = df.xs('Stage2b', level='param_policy')
	
	df.columns.name = 'week'
	df = df.stack('week').unstack('rand_seed')
	df = df.mean(axis=1)
	df = df.unstack('week')
	
	df = df.query('RolloutMonths != 8.0')
	df = df.unstack(splitParams)
	OutputToFile(df, visualDir + 'focus_data_in')
	
	metrics = []
	if median:
		metrics += ['50%']
	if mean:
		metrics += ['mean']
	if si:
		metrics += ['5%', '95%']
	
	smallFont = 20
	bigFont = 26
	
	
	df = df.describe(percentiles=[0.05, 0.95])
	df = df.loc[metrics].stack(splitParams).transpose()
	df.index = df.index.astype(float)
	df = df.sort_index(axis=0)
	df = df.sort_index(axis=1)
	
	plt.rcParams.update(plt.rcParamsDefault)
	
	ax = df.plot(figsize=(16.1, 10), linewidth=4, fontsize=smallFont)
	plt.grid(which='both')
	ax.set_ylim(0, 1500000)
	plt.legend(
		[
			'R0 2.5, No vaccination', 'R0 3.0, No vaccination',
			'R0 2.5, 12 month Rollout', 'R0 3.0, 12 month Rollout',
		],
		fontsize=bigFont)
	plt.xlabel("Week", fontsize=bigFont)
	plt.ylabel("Mean daily infections", fontsize=bigFont)
	ax.yaxis.set_major_formatter(lambda x, pos: '{:.1f}M'.format(x * 1e-6))
	plt.xticks([x*13 for x in range(9)])
	plt.show()
	#OutputToFile(df, visualDir + dataName + 'fullGraphPlot')


def MakeStageGraphs(dataDir, measureCols, filterParams, splitParam,
					median=True, mean=False, si=False):
	processDir = dataDir + '/ABM_process/'
	visualDir = dataDir + '/Graphs/'
	inputFile = processDir + 'processed_stage'
	
	df = pd.read_csv(
		inputFile + '.csv',
		index_col=list(range(3 + len(measureCols))),
		header=list(range(3)))
	
	df.index = df.index.droplevel(['run'])
	df.columns = df.columns.droplevel(['metric', 'cohort'])
	df = df.drop(columns=['0'])
	
	
	df = df.reorder_levels([1, 3, 4, 5, 6, 7, 8, 0, 2], axis=0)
	df = df.sort_index()
	
	for key in filterParams:
		df = df.xs(filterParams[key], level=key)
		
	df = df.applymap(lambda x: 100 if x >= 3 else 0)
	
	df = df.stack('day').unstack('rand_seed')
	df = df.mean(axis=1)
	df = df.unstack('day')
	
	df = df.unstack([splitParam])
	
	metrics = []
	if median:
		metrics += ['50%']
	if mean:
		metrics += ['mean']
	if si:
		metrics += ['5%', '95%']
	
	smallFont = 20
	bigFont = 26
	
	df = df.describe(percentiles=[0.05, 0.95])
	df = df.loc[metrics].stack(splitParam).transpose()
	df.index = df.index.astype(float)
	df = df.sort_index(axis=0)
	df = df.sort_index(axis=1)
	
	plt.rcParams.update(plt.rcParamsDefault)
	
	ax = df.plot(figsize=(16.1, 10), linewidth=4, fontsize=smallFont)
	plt.grid(which='both')
	ax.set_ylim(0, 105)
	plt.legend(['No vaccination', '8 month rollout',
				'12 month rollout', '16 month rollout'], fontsize=bigFont)
	plt.xlabel("Day", fontsize=bigFont)
	plt.ylabel("Time in lockdown", fontsize=bigFont)
	ax.yaxis.set_major_formatter(ticker.PercentFormatter())
	plt.xticks([x*13*7 for x in range(9)])
	plt.show()
	print(df)
