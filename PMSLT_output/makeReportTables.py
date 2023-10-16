
import pandas as pd
import numpy as np
import copy

import source.include.utilities as util
import source.shared as shared

DEFAULT_SOURCE = 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_09_27_nohsr2000'

scenarioSource = {
	'reform_kcl_all' : 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_10_11_kcl2000',
	'reform_kcl_10' : 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_10_11_kcl2000',
	'reform_kcl_nacl' : 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_10_11_kcl2000',
}

SCENE_MAP = {
	'reform_aus' : 'Mandatory - Australia (100% Compliance)',
	'reform_aus_90' : 'Australia 90% compliance',
	'reform_aus_70' : 'Australia 70% compliance',
	'reform_aus_50' : 'Australia 50% compliance',
	'reform_uk' : 'Mandatory UK (100% compliance)',
	'reform_uk_90' : 'UK 90% compliance',
	'reform_uk_70' : 'UK 70% compliance',
	'reform_uk_50' : 'UK 50% compliance',
	'reform_ausuk' : 'Mandatory Aus followed by UK (100% compliance)',
	'reform_ausuk_90' : 'Aus followed by UK, both 90% compliance',
	'reform_ausuk_70' : 'Aus followed by UK, both 70% compliance',
	'reform_ausuk_50' : 'Aus followed by UK, both 50% compliance',
	'reform_who' : 'Mandatory WHO',
	'reform_kcl_all' : '30% immediate substitution of all foods',
	'reform_kcl_10' : '10% substitution all foods, over 10 years',
	'reform_kcl_nacl' : '30% substitution discretionary over 3 years',
	'mass_media_uk' : 'UK mass media campaign',
	'package_uk' : 'UK salt reduction program',
}

HEADINGS = {
	'Reformulation' : [
		'reform_aus', 'reform_aus_90', 'reform_aus_70', 'reform_aus_50',
		'reform_uk', 'reform_uk_90', 'reform_uk_70', 'reform_uk_50',
		'reform_who',
	],
	'Substitution of NaCl with KCl' : [
		'reform_kcl_all', 'reform_kcl_10', 'reform_kcl_nacl',
	],
	'Programs' : [
		'mass_media_uk', 'package_uk',
	],
	'Extras' : [
		'reform_ausuk', 'reform_ausuk_90', 'reform_ausuk_70', 'reform_ausuk_50',
	],
}

DEF_INDEX = 3
DEF_HEADER = 2

outputTables = {}
outputTables['tableThree'] = {
	'description' : 'HALYs gained in [2024, 2044) discounted at 3%',
	'columns' : {
		'Combined' : {
			'file' : 'out_HALY_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'All'},
		},
		'SES 1' : {
			'file' : 'out_HALY_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'SES1'},
		},
		'SES 2' : {
			'file' : 'out_HALY_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'SES2'},
		},
		'SES 3' : {
			'file' : 'out_HALY_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'SES3'},
		},
		'SES 4' : {
			'file' : 'out_HALY_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'SES4'},
		},
		'SES 5' : {
			'file' : 'out_HALY_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'SES5'},
		},
		'RR SES 1 c.f. 5' : {
			'file' : 'standard/standard_age_haly_strata_discount_-0.03_year_ranges_deltaRatio_raw',
			'strata' : {'year_range' : '2024 to 2044'},
			'index' : 1, 'header' : 2,
		},
	},
}

outputTables['tableFour'] = copy.deepcopy(outputTables['tableThree'])
outputTables['tableFour']['description'] = 'HALYs gained over lifetime discounted at 3%'
for k, v in outputTables['tableFour']['columns'].items():
	if 'Year' in v['strata']:
		v['strata']['Year'] = 'All'
	else:
		outputTables['tableFour']['columns'][k] = {
			'numerator' : {
				'file' : 'out_HALY_year_year_0-114_discount_-0.03_raw',
				'strata' : {'Year' : 'All', 'Sex' : 'All', 'strata' : 'SES1'},
			},
			'denominator' : {
				'file' : 'out_HALY_year_year_0-114_discount_-0.03_raw',
				'strata' : {'Year' : 'All', 'Sex' : 'All', 'strata' : 'SES5'},
			},
			'skipUncertainty' : True
		}

outputTables['tableFive'] = {
	'description' : 'Expenditure in 2023 AU$ discounted at 3%',
	'columns' : {
		'Health - 20 Years' : {
			'file' : 'out_total_spent_pp_only_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'All'},
		},
		'Health - Lifetime' : {
			'file' : 'out_total_spent_pp_only_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : 'All', 'Sex' : 'All', 'strata' : 'All'},
		},
		'Health + Govt - 20 Years' : {
			'file' : 'out_total_spent_gov_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'All'},
		},
		'Health + Govt - Lifetime' : {
			'file' : 'out_total_spent_gov_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : 'All', 'Sex' : 'All', 'strata' : 'All'},
		},
		'Health + Govt + Industry - 20 Years' : {
			'file' : 'out_total_spent_gov_ind_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'All'},
		},
		'Health + Govt + Industry - Lifetime' : {
			'file' : 'out_total_spent_gov_ind_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : 'All', 'Sex' : 'All', 'strata' : 'All'},
		},
		'Health + Govt + Industry (conservative) - 20 Years' : {
			'file' : 'out_total_spent_gov_ind_conservative_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'All'},
		},
		'Health + Govt + Industry (conservative) - Lifetime' : {
			'file' : 'out_total_spent_gov_ind_conservative_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : 'All', 'Sex' : 'All', 'strata' : 'All'},
		},
	},
}

outputTables['tableSix'] = {
	'description' : 'Income gain in 2023 AU$ discounted at 3%',
	'inlineUncertainty' : True,
	'columns' : {
		'20-year time horizon' : {
			'file' : 'out_total_income_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'All'},
		},
		'Lifetime horizon' : {
			'file' : 'out_total_income_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : 'All', 'Sex' : 'All', 'strata' : 'All'},
		},
	},
}

outputTables['tableEight'] = {
	'description' : 'ICERs from health system and gov perspective, for years [2024, 2044), in 2023 AU$ discounted at 3%',
	'columns' : {
		'ICER + Gov 20 years' : {
			'file' : 'out_icer_gov_thousands_per_haly_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'All'},
			'costSaving' : True,
			'multiplier' : 1e3,
		},
		'HALY 20 years' : {
			'file' : 'out_HALY_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'All'},
		},
		'Health + Govt - 20 Years' : {
			'file' : 'out_total_spent_gov_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : '2024 to 2044', 'Sex' : 'All', 'strata' : 'All'},
		},
		'spacer1' : {'spacer' : True},
		'ICER + Gov All years' : {
			'file' : 'out_icer_gov_thousands_per_haly_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'costSaving' : True,
			'multiplier' : 1e3,
		},
		'HALY All years' : {
			'file' : 'out_HALY_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : 'All', 'Sex' : 'All', 'strata' : 'All'},
		},
		'Health + Govt - All Years' : {
			'file' : 'out_total_spent_gov_millions_year_year_0-114_discount_-0.03_raw',
			'strata' : {'Year' : 'All', 'Sex' : 'All', 'strata' : 'All'},
		},
	},
}

outputTables['tableNine'] = {
	'description' : 'Percentage reduction in ACMR gap from SES1 to SES5 in 2044',
	'inlineUncertainty' : True,
	'columns' : {
		'reduction in SES ACMR Gap ' : {
			'file' : 'standard/standard_age_acmr_strata_discount_-0.03_year_ranges_gainRatio_raw',
			'strata' : {'year_range' : '2044 to 2045'},
			'index' : 1, 'header' : 2,
			'formatType' : 'percentage',
		},
	},
}

outputTables['supTableOne'] = copy.deepcopy(outputTables['tableThree'])
outputTables['tableFour']['description'] = 'HALYs gained in [2024, 2044) discounted at 0%'
for k, v in outputTables['supTableOne']['columns'].items():
	if 'file' in v:
		v['file'] = v['file'].replace('-0.03', '0')
	else:
		v['numerator']['file'] = v['numerator']['file'].replace('-0.03', '0')
		v['denominator']['file'] = v['denominator']['file'].replace('-0.03', '0')

outputTables['supTableTwo'] = copy.deepcopy(outputTables['tableFour'])
outputTables['tableFour']['description'] = 'HALYs gained over lifetime discounted at 0%'
for k, v in outputTables['supTableTwo']['columns'].items():
	if 'file' in v:
		v['file'] = v['file'].replace('-0.03', '0')
	else:
		v['numerator']['file'] = v['numerator']['file'].replace('-0.03', '0')
		v['denominator']['file'] = v['denominator']['file'].replace('-0.03', '0')

outputTables['supTableThree'] = copy.deepcopy(outputTables['tableFive'])
outputTables['tableFour']['description'] = 'Expenditure in 2023 AU$ discounted at 0%'
for k, v in outputTables['supTableThree']['columns'].items():
	v['file'] = v['file'].replace('-0.03', '0')


def AddRowEntry(
		rows, data,
		formatType=False, multiplier=False, skipUncertainty=False,
		inlineUncertainty=False, costSaving=False, sigFigs=3):

	rows[0].append(shared.FormatNumber(data['50%'], multiplier, formatType, costSaving, sigFigs))
	uncertRow = 0 if inlineUncertainty else 1
	if skipUncertainty:
		rows[uncertRow].append(' ')
	else:
		entry = '({} to {})'.format(
			shared.FormatNumber(data['2.5%'], multiplier, formatType, costSaving, sigFigs),
			shared.FormatNumber(data['97.5%'], multiplier, formatType, costSaving, sigFigs))
		if entry == '(Cost Saving to Cost Saving)':
			entry = ' '
		rows[uncertRow].append(entry)


def GetDataEntry(rawName, dataSpec):
	if util.OptExists(dataSpec, 'numerator'):
		dfNum = GetDataEntry(rawName, dataSpec['numerator'])
		dfDenom = GetDataEntry(rawName, dataSpec['denominator'])
		return dfNum / dfDenom
		
	df = shared.ReadFromScenarioFiles(
		DEFAULT_SOURCE, scenarioSource, dataSpec['file'],
		index_col=list(range(util.Opt(dataSpec, 'index', DEF_INDEX))),
		header=list(range(util.Opt(dataSpec, 'header', DEF_HEADER)))
	)
	df = df[rawName]
	df = util.FilterOutMultiIndex(df, dataSpec['strata'])
	return df
	

def MakeTableRows(rawName, outName, tableData):
	if util.Opt(tableData, 'inlineUncertainty'):
		rows = [[]]
		rows[0].append(outName)
	else:
		rows = [[], []]
		rows[0].append(outName)
		rows[1].append(' ')
	
	for colName, colData in tableData['columns'].items():
		if util.Opt(colData, 'spacer'):
			rows[0].append(' ')
			if not util.Opt(tableData, 'inlineUncertainty'):
				rows[1].append(' ')
		else:
			df = GetDataEntry(rawName, colData)
			AddRowEntry(
				rows, df,
				multiplier=util.Opt(colData, 'multiplier'),
				formatType=util.Opt(colData, 'formatType'),
				skipUncertainty=util.Opt(colData, 'skipUncertainty'),
				inlineUncertainty=util.Opt(tableData, 'inlineUncertainty'),
				costSaving=util.Opt(colData, 'costSaving'),
				sigFigs=util.Opt(colData, 'sigFigs', 3),
			)
	return rows


def MakeTableHeader(tableData):
	return [[tableData['description']], [''] + list(tableData['columns'].keys()), ['=== Copyable table below ===']]


def MakeFormattedTable(tableName, tableData):
	rows = []
	rows = rows + MakeTableHeader(tableData)
	for headingName, headingMetrics in HEADINGS.items():
		rows.append([headingName])
		for rawName in headingMetrics: 
			outName = SCENE_MAP[rawName]
			rows = rows + MakeTableRows(rawName, outName, tableData)
	util.OutputRawRowsToFile(rows, 'reportOutput/{}'.format(tableName))


for tableName, tableData in outputTables.items():
	print('Making', tableName)
	MakeFormattedTable(tableName, tableData)
