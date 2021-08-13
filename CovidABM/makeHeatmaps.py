
import math
import pandas as pd
import numpy as np

from utilities import OutputToFile
from utilities import ToHeatmap
import utilities as util

############### Stages ###############

def DoMakeStagesHeatmap(
		subfolder, measureCols, heatStruct,
		stage_limit=2, start=0, window=100, describe=False):
	df = pd.read_csv(
		subfolder + '/Trace/processed_stage' + '.csv',
		index_col=list(range(2 + len(measureCols))),
		header=list(range(3)))
	
	prefixName = 'stageAbove_{}_from_{}_to_{}'.format(stage_limit, start, start + window)
	
	df = df.droplevel([0, 2], axis=1)
	df = df[[str(x) for x in range(start, start + window)]]
	df = df.apply(lambda c: [1 if x > stage_limit else 0 for x in c])
	
	df = df.mean(axis=1)
	util.MakeDescribedHeatmapSet(
		subfolder + '/Heatmaps/', df,
		heatStruct, prefixName, describe=describe)
	

def MakeStagesHeatmap(subfolder, measureCols, heatStruct, start, window, describe=False):
	DoMakeStagesHeatmap(
		subfolder, measureCols, heatStruct,
		stage_limit=2, start=start, window=window, describe=describe)
	
	
