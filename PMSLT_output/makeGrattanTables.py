
import pandas as pd
import numpy as np

import source.include.utilities as util
import source.shared as shared

DEFAULT_SOURCE = 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_09_27_nohsr2000'

EXTRA_DISCOUNT_YEARS = 4 # Takes us to 2023

scenarioSource = {
	'reform_kcl_all' : 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_10_11_kcl2000',
	'reform_kcl_10' : 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_10_11_kcl2000',
	'reform_kcl_nacl' : 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_10_11_kcl2000',
}

SCENE_MAP = {
	'bau' : 'BAU',
	'reform_aus' : 'Australia mandatory',
	'reform_aus_90' : 'Australia 90%',
	'reform_aus_70' : 'Australia 70%',
	'reform_aus_50' : 'Australia 50%',
	'reform_ausuk' : 'Aus then UK mandatory',
	'reform_ausuk_90' : 'Aus then UK 90%',
	'reform_ausuk_70' : 'Aus then UK 70%',
	'reform_ausuk_50' : 'Aus then UK 50%',
	'reform_kcl_all' : 'KCl subsitute (30%) envelope',
	'reform_kcl_10' : 'KCl subsitute (10%) all foods',
	'reform_kcl_nacl' : 'KCl subsitute (4.5%) discretionary',
	'reform_uk' : 'UK mandatory',
	'reform_uk_90' : 'UK 90%',
	'reform_uk_70' : 'UK 70%',
	'reform_uk_50' : 'UK 50%',
	'mass_media_uk' : 'UK mass media campaign',
	'package_uk' : 'UK salt reduction program',
	'reform_who' : 'Who mandatory',
	'none' : 'No change'
}

tablesToMake = {
	'halys'                                                         : {'file' : 'HALY', 'extraDiscountYears' : EXTRA_DISCOUNT_YEARS},
	'deaths'                                                        : {'file' : 'deaths', 'extraDiscountYears' : EXTRA_DISCOUNT_YEARS},
	'healthExpendGovIndConservativeMinusIncomeMillions'             : {'file' : 'total_spent_gov_ind_inc_conservative_millions', 'extraDiscountYears' : EXTRA_DISCOUNT_YEARS},
	'healthExpendGovIndMinusIncomeMillions'                         : {'file' : 'total_spent_gov_ind_inc_millions', 'extraDiscountYears' : EXTRA_DISCOUNT_YEARS},
	'healthExpendGovMillions'                                       : {'file' : 'total_spent_gov_millions', 'extraDiscountYears' : EXTRA_DISCOUNT_YEARS},
	'healthExpendMillions'                                          : {'file' : 'total_spent_pp_only_millions', 'extraDiscountYears' : EXTRA_DISCOUNT_YEARS},
	'ICERhealthExpendGovIndConservativeMinusIncomeThousandsPerHaly' : {'file' : 'icer_gov_ind_inc_conservative_thousands_per_haly'},
	'ICERhealthExpendGovIndMinusIncomeThousandsPerHaly'             : {'file' : 'icer_gov_ind_inc_thousands_per_haly'},
	'ICERhealthExpendGovThousandsPerHaly'                           : {'file' : 'icer_gov_thousands_per_haly'},
	'personIncomeMillions'                                          : {'file' : 'total_income_millions', 'extraDiscountYears' : EXTRA_DISCOUNT_YEARS},
	'personYears'                                                   : {'file' : 'person_years', 'extraDiscountYears' : EXTRA_DISCOUNT_YEARS},
	'strata_income_millions'                                        : {'file' : 'total_income_millions', 'extraDiscountYears' : EXTRA_DISCOUNT_YEARS, 'fullIndex' : True},
	'strata_halys'                                                  : {'file' : 'HALY', 'extraDiscountYears' : EXTRA_DISCOUNT_YEARS, 'fullIndex' : True},
}
	
def MakeUncertaintyFormatColumn(df, multiplier=1):
	df = df.apply(lambda x: '{} ({} to {})'.format(
		shared.FormatNumber(x['50%'], multiplier, False, False, 3),
		shared.FormatNumber(x['2.5%'], multiplier, False, False, 3),
		shared.FormatNumber(x['97.5%'], multiplier, False, False, 3)), axis=1)
	return df
	

def MakeDiscountTable(name, outName, raw=False, filterOut=False, extraDiscountYears=0):
	toAppend = []
	for discount in [0, -0.03]:
		discountMult = ((1 + discount)**(-extraDiscountYears))
		if raw:
			fileName = 'out_{}_year_year_0-114_discount_{}_raw'.format(name, discount)
			df = shared.ReadFromScenarioFiles(
				DEFAULT_SOURCE, scenarioSource, fileName,
				index_col=list(range(3)), header=list(range(2)))
			df.columns.names = ['Scenario', 'Percentile']
			if filterOut:
				df = util.FilterOutMultiIndex(df, {name : 'All' for name in filterOut})
			df = util.FilterOutMultiIndex(df.transpose(), {'Percentile' : '50%'}).transpose()
			df = df * discountMult
		else:
			fileName = 'out_{}_year_year_0-114_discount_{}_raw'.format(name, discount)
			df = shared.ReadFromScenarioFiles(
				DEFAULT_SOURCE, scenarioSource, fileName,
				index_col=list(range(3)), header=list(range(2)))
			df.columns.names = ['Scenario', 'Percentile']
			
			if filterOut:
				df = util.FilterOutMultiIndex(df, {name : 'All' for name in filterOut})
			
			df = pd.DataFrame({name : MakeUncertaintyFormatColumn(df[name], multiplier=discountMult) 
				 for name in df.columns.get_level_values('Scenario')
			})
		
		df = df[util.ListIntersection(list(df.columns), SCENE_MAP.keys())]
		df = df.rename(columns=SCENE_MAP)
		df.columns.name = 'Scenario'
		df = df.transpose()
		df = util.AddIndexLevel(df, 'Discount', '{:.0f}%'.format(-100*discount), toTopLevel=True)
		toAppend.append(df)
	
	df = pd.concat(toAppend)
	if isinstance(df.columns, pd.MultiIndex):
		toUnstack = util.ListRemove(df.columns.names, 'Year')
		df = df.stack(toUnstack)
	return df


def MakeStandardTable(
		name, outName, suffix=False, hasPercentile=True,
		filterOut=False, extraDiscountYears=0):
	toAppend = []
	for raw in ([False, True] if hasPercentile else [False]):
		df = MakeDiscountTable(
			name, outName, raw=raw, filterOut=filterOut,
			extraDiscountYears=extraDiscountYears)
		df = util.AddIndexLevel(df, 'Raw Median', raw, toTopLevel=True)
		toAppend.append(df)
	df = pd.concat(toAppend)
	df = df.sort_index(axis=1).sort_index(axis=0)
	util.OutputToFile(df, 'output{}/{}{}'.format(
		('_' + suffix) if suffix else '',
		outName,
		('_' + suffix) if suffix else ''
	))
	

for outName, outData in tablesToMake.items():
	filterOut = False if util.Opt(outData, 'fullIndex') else ['Sex', 'strata']
	extraDiscountYears = util.Opt(outData, 'extraDiscountYears', 0)
	print(outName)
	MakeStandardTable(
		outData['file'], outName, suffix=False, hasPercentile=True,
		filterOut=filterOut, extraDiscountYears=extraDiscountYears)
				  