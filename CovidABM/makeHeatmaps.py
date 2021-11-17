
import math
import pandas as pd
import numpy as np

from utilities import OutputToFile
from utilities import ToHeatmap
import utilities as util

############### Stages ###############

def DoMakeStagesHeatmap(
		subfolder, measureCols, heatStruct,
		stage_min=3, stage_max=4, start=0, window=100, describe=False):
	df = pd.read_csv(
		subfolder + '/Traces/processed_stage' + '.csv',
		index_col=list(range(2 + len(measureCols))),
		header=list(range(3)))
	
	prefixName = 'stageMin_{}_max_{}_from_{}_to_{}'.format(
		stage_min, stage_max, start, start + window)
	
	df = df.droplevel([0, 2], axis=1)
	df = df[[str(x) for x in range(start, start + window)]]
	df = df.apply(lambda c: [1 if x >= stage_min and x <= stage_max else 0 for x in c])
	
	df = df.mean(axis=1)
	df = df.droplevel('run', axis=0)
	
	util.MakeDescribedHeatmapSet(
		subfolder + '/Heatmaps/', df,
		heatStruct, prefixName, describe=describe)
	

def MakeStagesHeatmap(
		subfolder, measureCols, heatStruct, start, window,
		stage_set=False, describe=False):
	
	stage_min = 3
	stage_max = 4
	if stage_set is not False:
		stage_min = stage_set
		stage_max = stage_set
	
	DoMakeStagesHeatmap(
		subfolder, measureCols, heatStruct,
		stage_min=stage_min, stage_max=stage_max,
		start=start, window=window, describe=describe)


def OutputHeatmapIndexComparision(
		subfolder, heatStruct, df, fileName, indexName, baseName, divide=True):
	
	isColIndex = indexName in [x[0] for x in heatStruct.get('sort_cols')]
	if not isColIndex:
		df = df.transpose()
	else:
		baseName = str(baseName)
	
	oldOrder = list(df.columns.names)
	if None in oldOrder:
		oldOrder = ['metric'] + util.ListRemove(oldOrder, None)
		df.columns.names = oldOrder
	
	df = df.reorder_levels([indexName] + util.ListRemove(oldOrder, indexName), axis=1)
	
	indexValues = util.ListUnique([x[0] for x in df.columns])
	if len(indexValues) <= 1:
		# Do not make comparision for an index with no variance.
		return
	
	if baseName not in indexValues:
		print('Warning: baseName {} not in index {}.'.format(baseName, indexName))
		return
	
	for indexVal in util.ListRemove(indexValues, baseName):
		if divide:
			df[indexVal] = df[indexVal].divide(df[baseName], axis=0)
		else:
			df[indexVal] = df[indexVal].subtract(df[baseName], axis=0)
	
	if divide:
		df[baseName] = df[baseName].divide(df[baseName], axis=0)
	else:
		df[baseName] = df[baseName].subtract(df[baseName], axis=0)
	
	df = df.reorder_levels(oldOrder, axis=1)
		
	if not isColIndex:
		df = df.transpose()
	outputName = 'compare_{}_{}_{}_{}'.format(
		indexName, baseName,
		'divide' if divide else 'subtract',fileName)
	
	print(outputName)
	OutputToFile(df, subfolder + outputName, head=False)
	
	
def MakeComparisionHeatmap(subfolder, heatStruct, fileName, divide=True):
	index_rows = heatStruct.get('index_rows')
	index_cols = heatStruct.get('index_cols')
	
	df = pd.read_csv(
		subfolder + '/Heatmaps/' + fileName + '.csv',
		index_col=list(range(len(index_rows))),
		header=list(range(len(index_cols) + 1)))
	df = df.drop_duplicates()
	
	for indexEntry in heatStruct.get('sort_rows') + heatStruct.get('sort_cols'):
		name = indexEntry[0]
		sort = indexEntry[1]
		if len(sort) > 1:
			if 'base_value' in heatStruct and name in heatStruct.get('base_value'):
				baseIndexName = heatStruct.get('base_value').get(name)
			else:
				baseIndexName = list(sort.keys())[0]
			OutputHeatmapIndexComparision(
				subfolder + '/Heatmaps/', heatStruct, df, fileName,
				name, baseIndexName, divide=divide)
	
	