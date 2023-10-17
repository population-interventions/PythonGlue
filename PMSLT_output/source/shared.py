
import pandas as pd
import numpy as np

import source.include.utilities as util

costPath = 'C:/Dev/Repos/QPMSLT/pmsltInput/salt/data/salt/costs'
inputCache = []

DISCOUNT_START = 2023
MAX_YEAR = 2132

costFixConf = {
	'mass_media_uk'   : {'file' : 'mass_media_uk', 'gov' : 1, 'ind' : 1},
	'package_uk'      : {'list' : ['reform_uk', 'mass_media_uk']},
	'reform_aus'      : {'file' : 'reform_aus_100', 'conservative' : 'reform_aus_conservative_100', 'gov' : 1, 'ind' : 1},
	'reform_aus_50'   : {'file' : 'reform_aus_100', 'conservative' : 'reform_aus_conservative_100', 'gov' : 1, 'ind' : 0.5},
	'reform_aus_70'   : {'file' : 'reform_aus_100', 'conservative' : 'reform_aus_conservative_100', 'gov' : 1, 'ind' : 0.7},
	'reform_aus_90'   : {'file' : 'reform_aus_100', 'conservative' : 'reform_aus_conservative_100', 'gov' : 1, 'ind' : 0.9},
	'reform_ausuk'    : {'file' : 'reform_aus_uk_combined_100', 'conservative' : 'reform_aus_uk_combined_conservative_100', 'gov' : 1, 'ind' : 1},
	'reform_ausuk_50' : {'file' : 'reform_aus_uk_combined_100', 'conservative' : 'reform_aus_uk_combined_conservative_100', 'gov' : 1, 'ind' : 0.5},
	'reform_ausuk_70' : {'file' : 'reform_aus_uk_combined_100', 'conservative' : 'reform_aus_uk_combined_conservative_100', 'gov' : 1, 'ind' : 0.7},
	'reform_ausuk_90' : {'file' : 'reform_aus_uk_combined_100', 'conservative' : 'reform_aus_uk_combined_conservative_100', 'gov' : 1, 'ind' : 0.9},
	'reform_kcl_10'   : {'file' : 'reform_kcl_10', 'gov' : 1, 'ind' : 1},
	'reform_kcl_all'  : {'file' : 'reform_kcl_30', 'gov' : 1, 'ind' : 1},
	'reform_kcl_nacl' : {'file' : 'reform_kcl_nacl', 'gov' : 1, 'ind' : 1},
	'reform_uk'       : {'file' : 'reform_uk_100', 'conservative' : 'reform_uk_conservative_100', 'gov' : 1, 'ind' : 1},
	'reform_uk_50'    : {'file' : 'reform_uk_100', 'conservative' : 'reform_uk_conservative_100', 'gov' : 1, 'ind' : 1},
	'reform_uk_70'    : {'file' : 'reform_uk_100', 'conservative' : 'reform_uk_conservative_100', 'gov' : 1, 'ind' : 1},
	'reform_uk_90'    : {'file' : 'reform_uk_100', 'conservative' : 'reform_uk_conservative_100', 'gov' : 1, 'ind' : 1},
	'reform_who'      : {'file' : 'reform_who_100', 'conservative' : 'reform_who_conservative_100','gov' : 1, 'ind' : 1},
	'reform_who_50'   : {'file' : 'reform_who_100', 'conservative' : 'reform_who_conservative_100','gov' : 1, 'ind' : 1},
	'reform_who_70'   : {'file' : 'reform_who_100', 'conservative' : 'reform_who_conservative_100','gov' : 1, 'ind' : 1},
	'reform_who_90'   : {'file' : 'reform_who_100', 'conservative' : 'reform_who_conservative_100','gov' : 1, 'ind' : 1},
}

scenarioSource = {
	'reform_kcl_all' : 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_10_11_kcl2000',
	'reform_kcl_10' : 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_10_11_kcl2000',
	'reform_kcl_nacl' : 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_10_11_kcl2000',
}

yearRangeMap = {
	'2024 to 2034' : [2024, 2034],
	'2024 to 2044' : [2024, 2044],
	'2034 to 2044' : [2034, 2044],
}


def FormatNumber(number, multiplier, formatType, costSaving, sigFigs):
	if multiplier is not False:
		number = number*multiplier
	if costSaving and number < 0:
		return 'Cost Saving'
	if formatType == 'percentage':
		return util.RoundNumber(number*100, sigFigs) + '%'
	return util.RoundNumber(number, sigFigs)


def GetFileDiscount(file):
	fileData = file.split('_')
	index = fileData.index('discount')
	if (not index) or len(fileData) < index + 1:
		return False
	discount = float(fileData[index + 1])
	return discount


def LoadCostFile(costFile):
	global inputCache
	if costFile in inputCache:
		return inputCache[costFile]
	df = util.LoadCleanCsv('{}/{}'.format(costPath, costFile))
	df = df.set_index('year')
	df = util.ExpandAgeCategory(
		df, MAX_YEAR, targetColumn='year', ignoreMissingZero=True,
		ignoreLengthCheck=True)
	df = df*1e-6 # Output is in millions
	df.index.name = 'year'
	return df


def AggregateCosts(df, dfCost, yearRange, discount):
	if discount is not False and discount != 0:
		dfCost = dfCost.copy()
		discountTime = dfCost.index.values - DISCOUNT_START
		dfCost = dfCost * (1 + discount) ** discountTime
	totalCost = util.FilterOnIndex(dfCost, 'year', yearRange[1], MAX_YEAR).sum()
	return totalCost


def FixRangeName(df, dfCost, yearRange, discount):
	df = df - AggregateCosts(df, dfCost, yearRange, discount)
	return df

		
def AdjustScenarioCost(df, dfCost, discount):
	df = df.transpose()
	
	for rangeName, yearRange in yearRangeMap.items():
		df[rangeName] = FixRangeName(df[rangeName], dfCost, yearRange, discount)
	
	df = df.transpose()
	return df


def FixScenario(fileName, df, scenario, discount):
	if not util.OptExists(costFixConf, scenario):
		return df
	scenarioConf = costFixConf[scenario]
	if util.OptExists(scenarioConf, 'list'):
		for otherScenario in util.Opt(scenarioConf, 'list'):
			df = FixScenario(fileName, df, otherScenario, discount)
		return df
	
	costFile = scenarioConf['file']
	if '_conservative_' in fileName and util.OptExists(scenarioConf, 'conservative'):
		costFile = scenarioConf['conservative']
	dfCost = LoadCostFile(costFile)
	
	for metric in ['gov', 'ind']:
		if '_{}_'.format(metric) in fileName:
			df = AdjustScenarioCost(df, dfCost[metric]*scenarioConf[metric], discount)
	
	return df


def LoadFile(source, fileName, index_col, header):
	df = pd.read_csv('{}/{}.csv'.format(source, fileName), index_col=index_col, header=header)
	for scenario, directory in scenarioSource.items():
		dfAlt = pd.read_csv('{}/{}.csv'.format(directory, fileName), index_col=index_col, header=header)
		df[scenario] = dfAlt[scenario]
	return df

def FixFile(df, fileName):
	discount = GetFileDiscount(fileName)
	scenarios = list(set(df.columns.get_level_values(0)))
	for scenario in scenarios:
		df[scenario] = FixScenario(fileName, df[scenario], scenario, discount)
	
	return df


def FixIcerFile(df, dfRawCost, fileName, costFile):
	dfFixedCost = FixFile(dfRawCost.copy(), costFile)
	ratio = dfFixedCost / dfRawCost
	df = df * ratio
	return df


def ReadFromScenarioFiles(source, fileName, index_col=list(range(1)), header=list(range(1))):
	df = LoadFile(source, fileName, index_col, header)
	
	if 'out_total_spent_gov' in fileName:
		df = FixFile(df, fileName)
	
	if 'out_icer_gov' in fileName:
		costFile = fileName.replace('out_icer_gov', 'out_total_spent_gov').replace('thousands_per_haly', 'millions')
		dfRawCost = LoadFile(source, costFile, index_col, header)
		df = FixIcerFile(df, dfRawCost, fileName, costFile)
		
	return df

