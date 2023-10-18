
import pandas as pd
import numpy as np
import copy

import source.include.utilities as util
import source.shared as shared

DEFAULT_SOURCE = 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_09_27_nohsr2000'

EXTRA_DISCOUNT_YEARS = 4 # Takes us to 2023

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
		'reform_who', 'reform_ausuk',
	],
	'Substitution of NaCl with KCl' : [
		'reform_kcl_all', 'reform_kcl_10', 'reform_kcl_nacl',
	],
	'Programs' : [
		'mass_media_uk', 'package_uk',
	],
	'Extras' : [
		'reform_ausuk_90', 'reform_ausuk_70', 'reform_ausuk_50',
	],
}

DEF_INDEX = 5
DEF_HEADER = 2

outputTables = {}

outputTables['healthExpenseFigure'] = {
	'description' : 'Health expenditure discounted at 3% for a table',
	'inlineUncertainty' : True,
	'ignoreHeadings' : True,
	'spaceBetweenScenarios' : 1,
	'columns' : {
		'Health + Govt - 20 Years' : {
			'file' : 'out_total_spent_gov_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
			'rawValues' : True,
		},
		'Health + Govt - Lifetime' : {
			'file' : 'out_total_spent_gov_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2019, 'End Year' : 2133, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
			'rawValues' : True,
		},
	},
}

outputTables['tableThree'] = {
	'description' : 'HALYs gained in [2024, 2044) discounted at 3%',
	'columns' : {
		'Combined' : {
			'file' : 'out_HALY_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'SES 1' : {
			'file' : 'out_HALY_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'SES1'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'SES 2' : {
			'file' : 'out_HALY_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'SES2'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'SES 3' : {
			'file' : 'out_HALY_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'SES3'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'SES 4' : {
			'file' : 'out_HALY_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'SES4'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'SES 5' : {
			'file' : 'out_HALY_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'SES5'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
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
	if 'Start Year' in v['strata']:
		v['strata']['Start Year'] = 2019
		v['strata']['End Year'] = 2133
	else:
		outputTables['tableFour']['columns'][k] = {
			'numerator' : {
				'file' : 'out_HALY_age_stacked_discount_-0.03_raw',
				'strata' : {'Start Year' : 2019, 'End Year' : 2133, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'SES1'},
			},
			'denominator' : {
				'file' : 'out_HALY_age_stacked_discount_-0.03_raw',
				'strata' : {'Start Year' : 2019, 'End Year' : 2133, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'SES5'},
			},
			'skipUncertainty' : True
		}

outputTables['tableSeven'] = {
	'description' : 'Expenditure in 2023 AU$ discounted at 3%',
	'columns' : {
		'Health - 20 Years' : {
			'file' : 'out_total_spent_pp_only_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'Health - Lifetime' : {
			'file' : 'out_total_spent_pp_only_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2019, 'End Year' : 2133, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'Health + Govt - 20 Years' : {
			'file' : 'out_total_spent_gov_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'Health + Govt - Lifetime' : {
			'file' : 'out_total_spent_gov_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2019, 'End Year' : 2133, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'Health + Govt + Industry - 20 Years' : {
			'file' : 'out_total_spent_gov_ind_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'Health + Govt + Industry - Lifetime' : {
			'file' : 'out_total_spent_gov_ind_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2019, 'End Year' : 2133, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'Health + Govt + Industry (conservative) - 20 Years' : {
			'file' : 'out_total_spent_gov_ind_conservative_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'Health + Govt + Industry (conservative) - Lifetime' : {
			'file' : 'out_total_spent_gov_ind_conservative_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2019, 'End Year' : 2133, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
	},
}

outputTables['tableEight'] = {
	'description' : 'Income gain in 2023 AU$ discounted at 3%',
	'inlineUncertainty' : True,
	'columns' : {
		'20-year time horizon' : {
			'file' : 'out_total_income_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
		'Lifetime horizon' : {
			'file' : 'out_total_income_millions_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2019, 'End Year' : 2133, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'extraDiscountYears' : EXTRA_DISCOUNT_YEARS,
		},
	},
}

outputTables['tableNine'] = {
	'description' : 'Incremental cost effectiveness ratio (each intervention c.f. BAU; Aus$ per HALY gained) from the Health + Govt Expenditure perspective, 3% discount rate: 20 year and lifetime horizons',
	'columns' : {
		'ICER + Gov 20 years' : {
			'file' : 'out_icer_gov_thousands_per_haly_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2024, 'End Year' : 2044, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'costSaving' : True,
			'multiplier' : 1e3,
		},
		'ICER + Gov All years' : {
			'file' : 'out_icer_gov_thousands_per_haly_age_stacked_discount_-0.03_raw',
			'strata' : {'Start Year' : 2019, 'End Year' : 2133, 'Age' : 'All', 'Sex' : 'All', 'strata' : 'All'},
			'costSaving' : True,
			'multiplier' : 1e3,
		},
	},
}

outputTables['tableFive'] = {
	'description' : 'Percentage reduction in ACMR gap from SES1 to SES5 in 2044',
	'inlineUncertainty' : True,
	'columns' : {
		'SES1' : {
			'file' : 'standard/standard_age_acmr_strata_discount_-0.03_year_ranges_directRatio_raw',
			'strata' : {'year_range' : '2044 to 2045', 'strata' : 'SES1'},
			'index' : 2, 'header' : 2,
			'formatType' : 'percentage',
			'oneMinus' : True,
			'skipUncertainty' : True,
		},
		'SES5' : {
			'file' : 'standard/standard_age_acmr_strata_discount_-0.03_year_ranges_directRatio_raw',
			'strata' : {'year_range' : '2044 to 2045', 'strata' : 'SES5'},
			'index' : 2, 'header' : 2,
			'formatType' : 'percentage',
			'oneMinus' : True,
			'skipUncertainty' : True,
		},
		'reduction in SES ACMR Gap ' : {
			'file' : 'standard/standard_age_acmr_strata_discount_-0.03_year_ranges_gainRatio_raw',
			'strata' : {'year_range' : '2044 to 2045'},
			'index' : 1, 'header' : 2,
			'formatType' : 'percentage',
		},
	},
}

outputTables['supTableOne'] = copy.deepcopy(outputTables['tableThree'])
outputTables['supTableOne']['description'] = 'HALYs gained in [2024, 2044) discounted at 0%'
for k, v in outputTables['supTableOne']['columns'].items():
	if 'file' in v:
		v['file'] = v['file'].replace('-0.03', '0')
	else:
		v['numerator']['file'] = v['numerator']['file'].replace('-0.03', '0')
		v['denominator']['file'] = v['denominator']['file'].replace('-0.03', '0')

outputTables['supTableTwo'] = copy.deepcopy(outputTables['tableFour'])
outputTables['supTableTwo']['description'] = 'HALYs gained over lifetime discounted at 0%'
for k, v in outputTables['supTableTwo']['columns'].items():
	if 'file' in v:
		v['file'] = v['file'].replace('-0.03', '0')
	else:
		v['numerator']['file'] = v['numerator']['file'].replace('-0.03', '0')
		v['denominator']['file'] = v['denominator']['file'].replace('-0.03', '0')

outputTables['supTableThree'] = copy.deepcopy(outputTables['tableSeven'])
outputTables['supTableThree']['description'] = 'Expenditure in 2023 AU$ discounted at 0%'
for k, v in outputTables['supTableThree']['columns'].items():
	v['file'] = v['file'].replace('-0.03', '0')

outputTables['supTableFour'] = copy.deepcopy(outputTables['tableEight'])
outputTables['supTableFour']['description'] = 'Income gain in 2023 AU$ discounted at 0%'
for k, v in outputTables['supTableFour']['columns'].items():
	v['file'] = v['file'].replace('-0.03', '0')


def MaybeFormatNumber(number, multiplier, formatType, costSaving, sigFigs, wantRaw):
	if wantRaw:
		return str(number*multiplier)
	return shared.FormatNumber(number, multiplier, formatType, costSaving, sigFigs)

	
def AddRowEntry(
		rows, data,
		formatType=False, multiplier=False, skipUncertainty=False,
		inlineUncertainty=False, costSaving=False, sigFigs=3, wantRaw=False):

	rows[0].append(MaybeFormatNumber(data['50%'], multiplier, formatType, costSaving, sigFigs, wantRaw))
	uncertRow = 0 if inlineUncertainty else 1
	if skipUncertainty:
		if not inlineUncertainty:
			rows[uncertRow].append(' ')
	else:
		baseString = '{}\t{}' if wantRaw else '({} to {})'
		entry = baseString.format(
			MaybeFormatNumber(data['2.5%'], multiplier, formatType, costSaving, sigFigs, wantRaw),
			MaybeFormatNumber(data['97.5%'], multiplier, formatType, costSaving, sigFigs, wantRaw))
		if entry == '(Cost Saving to Cost Saving)':
			entry = ' '
		rows[uncertRow].append(entry)


def GetDataEntry(rawName, dataSpec):
	if util.OptExists(dataSpec, 'numerator'):
		dfNum = GetDataEntry(rawName, dataSpec['numerator'])
		dfDenom = GetDataEntry(rawName, dataSpec['denominator'])
		return dfNum / dfDenom
		
	df = shared.ReadFromScenarioFiles(
		DEFAULT_SOURCE, dataSpec['file'],
		index_col=list(range(util.Opt(dataSpec, 'index', DEF_INDEX))),
		header=list(range(util.Opt(dataSpec, 'header', DEF_HEADER)))
	)
	df = df[rawName]
	df = util.FilterOutMultiIndex(df, dataSpec['strata'])
	return df


def PostProcessDataEntry(df, oneMinus=False):
	if oneMinus:
		df = 1 - df
	return df
	

def MakeTableRows(rawName, outName, tableData):
	if util.Opt(tableData, 'inlineUncertainty'):
		rows = [[]]
		rows[0].append(outName)
	else:
		rows = [[], []]
		rows[0].append(outName)
		rows[1].append('')
	
	for colName, colData in tableData['columns'].items():
		discountMult = 1
		if util.OptExists(colData, 'extraDiscountYears'):
			discount = shared.GetFileDiscount(colData['file'])
			discountMult = ((1 + discount)**(-util.Opt(colData, 'extraDiscountYears')))
		
		if util.Opt(colData, 'spacer'):
			rows[0].append('')
			if not util.Opt(tableData, 'inlineUncertainty'):
				rows[1].append('')
		else:
			df = GetDataEntry(rawName, colData)
			df = PostProcessDataEntry(df, oneMinus=util.Opt(colData, 'oneMinus'))
			AddRowEntry(
				rows, df,
				multiplier=util.Opt(colData, 'multiplier', 1) * discountMult,
				formatType=util.Opt(colData, 'formatType'),
				skipUncertainty=util.Opt(colData, 'skipUncertainty'),
				inlineUncertainty=util.Opt(tableData, 'inlineUncertainty'),
				costSaving=util.Opt(colData, 'costSaving'),
				sigFigs=util.Opt(colData, 'sigFigs', 3),
				wantRaw=util.Opt(colData, 'rawValues'),
			)
	return rows


def MakeTableHeader(tableData):
	return [[tableData['description']], [''] + list(tableData['columns'].keys()), ['=== Copyable table below ===']]


def MakeFormattedTable(tableName, tableData):
	rows = []
	rows = rows + MakeTableHeader(tableData)
	for headingName, headingMetrics in HEADINGS.items():
		if not util.Opt(tableData, 'ignoreHeadings'):
			rows.append([headingName])
		for rawName in headingMetrics: 
			outName = SCENE_MAP[rawName]
			rows = rows + MakeTableRows(rawName, outName, tableData)
			for i in range(util.Opt(tableData, 'spaceBetweenScenarios', 0)):
				rows.append([' '])
	util.OutputRawRowsToFile(rows, 'reportOutput/{}'.format(tableName))

outputTables = {'healthExpenseFigure' : outputTables['healthExpenseFigure']}
for tableName, tableData in outputTables.items():
	print('Making', tableName)
	MakeFormattedTable(tableName, tableData)
