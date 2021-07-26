
import math
import pandas as pd
import numpy as np

from utilities import OutputToFile
from utilities import ToHeatmap
from processedOutputToReport import OutputLineCompare


def HeatmapProcessNoRollout(df, heatmapStructure):
	df = df.reset_index()

	df = ToHeatmap(df, heatmapStructure)
	
	df = df[df.index.get_level_values('Var_R0_mult') != 1.45]
	df = df.transpose()
	df = df[df.index.get_level_values('VacEfficacy') != 0.875]
	df = df.transpose()
	
	return df


def HeatmapProcess(df, heatmapStructure):
	df = df.reset_index()

	df = ToHeatmap(df, heatmapStructure)
	
	df = df[df.index.get_level_values('Var_R0_mult') != 1.45]
	df = df.transpose()
	df = df[df.index.get_level_values('VacEfficacy') != 0.875]
	df = df.transpose()
	
	return df

	
def SmartFormat(x):
	if x > 1 or x < -1:
		return '{:,.2f}'.format(x/1000)
	return '{:,.2f}%'.format(x*100)


def ShapeMedianTable(df, measure, toSort):
	df = df.transpose()[measure]
	df = df.unstack('RolloutMonths')
	df = df.reset_index().set_index(toSort).sort_index()
	return df

def OutputMedianUncertainTables(df, outFile, toSort):
	df = df.describe(percentiles=[0.05, 0.95])
	df_med = ShapeMedianTable(df, '50%', toSort).applymap(SmartFormat)
	df_upper = ShapeMedianTable(df, '95%', toSort).applymap(SmartFormat)
	df_lower = ShapeMedianTable(df, '5%', toSort).applymap(SmartFormat)
	df_out = df_med + ' (' + df_lower + ' to ' + df_upper + ')'
	OutputToFile(df_out, outFile)

   
def ProcessGDP(subfolder, measureCols):
	gdp_effects = pd.read_csv(subfolder + '/other_input/gdp_cost' + '.csv',
				header=[0])
	gdp_effects = gdp_effects.set_index(['stage'])
	
	stageFile = subfolder + '/Report_process/average_seeds_stage'
	stageDf = pd.read_csv(
		stageFile + '.csv', 
		index_col=list(range(1 + len(measureCols))),
		header=[0, 1])
	
	stageDf = stageDf.transpose().reorder_levels([1, 0], axis=0).unstack('year') * 365 / 7
	stageDf = stageDf.mul(gdp_effects['gdpPerWeek'], axis=0).transpose()
	stageDf = stageDf.unstack(['RolloutMonths']).groupby(level=[1], axis=1).sum()
	stageDf = stageDf.unstack('year').reorder_levels([1, 0], axis=1)
	stageDf = stageDf['0'] + stageDf['1']
	return stageDf
	
	
def ProcessHealthPerspective(
		df, heatmapStructure, reportDir, subfolder,
		measureCols, healthPerspectiveRows, addGDP=False):
	df = df['life']
	df_HALY = df['HALY']
	df_HALY_diff = df_HALY.sub(df_HALY[0.0], axis=0) * -1
	df_spent = df['spent']
	df_spent_diff = df_spent.sub(df_spent[0.0], axis=0)
	
	gdpCost = ProcessGDP(subfolder, measureCols)
	gdpCost_diff = gdpCost.sub(gdpCost[0.0], axis=0)
	
	df_ICER = (df_spent_diff[12] + 1.2 * 10**9) / df_HALY_diff[12]
	df_spend_to_8 = 1300 * (df_HALY[12] - df_HALY[8]) - (df_spent[12] - df_spent[8])
	if addGDP:
		df_ICER = df_ICER + gdpCost_diff[12] / df_HALY_diff[12]
		df_spend_to_8 = df_spend_to_8 - (gdpCost[12] - gdpCost[8])
	
	df_full = pd.DataFrame({'ICER' : df_ICER, 'spendTo8' : df_spend_to_8})

	path = reportDir + 'health_perspective'
	heatmapPath = subfolder + '/PMSLT_heatmaps/ICER'
	if addGDP:
		path = path + '_add_gdp'
		heatmapPath = heatmapPath + '_add_gdp'
	
	OutputToFile(HeatmapProcessNoRollout(df_ICER, heatmapStructure), heatmapPath)
	
	def SmartFormat(x, exponent=10**6):
		if abs(x) > 10**6:
			return '{:,.1f}'.format(x/10**6)
		return '{:,.0f}'.format(x)
	
	for values in healthPerspectiveRows:
		OutputLineCompare(df_full, False, False, path, *values, formatFunc=SmartFormat)
	

def ProcessPMSLTResults(dataDir, measureCols, heatmapStructure, healthPerspectiveRows):
	print('ProcessPMSLTResults')
	processDir = dataDir + '/PMSLT_out/'
	reportDir = dataDir + '/Report_out/'
	
	df = pd.read_csv(
		processDir + 'PMSLT_out' + '.csv',
		index_col=list(range(1 + len(measureCols))),
		header=list(range(2)))
	
	print('HeatmapProcess')
	OutputToFile(
		HeatmapProcess(df[[['life', 'deaths']]].stack('measure'), heatmapStructure),
		dataDir + '/PMSLT_heatmaps/deaths')
	
	df = df.unstack('RolloutMonths')
	df = df.reorder_levels([2, 1, 0], axis=1)
	df_vac = df.sub(df[0], axis=0) * -1
	
	df_vac = df_vac.reorder_levels([2, 1, 0], axis=1)
	df = df.reorder_levels([2, 1, 0], axis=1)
	
	print('ProcessHealthPerspective')
	ProcessHealthPerspective(
		df, heatmapStructure, reportDir, dataDir,
		measureCols, healthPerspectiveRows, False)
	ProcessHealthPerspective(
		df, heatmapStructure, reportDir, dataDir,
		measureCols, healthPerspectiveRows, True)
	
	print('OutputMedianUncertainTables')
	OutputMedianUncertainTables(df, reportDir + 'pmslt_describe', ['measure', 'period'])
	OutputMedianUncertainTables(df_vac, reportDir + 'pmslt_describe_diff', ['measure', 'period'])
