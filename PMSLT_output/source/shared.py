
import pandas as pd
import numpy as np

import source.include.utilities as util

def FormatNumber(number, multiplier, formatType, costSaving, sigFigs):
	if multiplier is not False:
		number = number*multiplier
	if costSaving and number < 0:
		return 'Cost Saving'
	if formatType == 'percentage':
		return util.RoundNumber(number*100, sigFigs) + '%'
	return util.RoundNumber(number, sigFigs)


def ReadFromScenarioFiles(source, scenarioSource, fileName, index_col=list(range(1)), header=list(range(1))):
	df = pd.read_csv('{}/{}.csv'.format(source, fileName), index_col=index_col, header=header)
	for scenario, directory in scenarioSource.items():
		dfAlt = pd.read_csv('{}/{}.csv'.format(directory, fileName), index_col=index_col, header=header)
		df[scenario] = dfAlt[scenario]
	return df
