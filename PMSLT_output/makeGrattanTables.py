
import pandas as pd
import numpy as np

import source.include.utilities as util

SOURCE = 'C:/dr/PI_SHINE Protocols_Reports/B01_Salt Modelling Grattan/Output/2023_09_27_nohsr2000'


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
	'HALY' : 'halys',
	'deaths' : 'deaths',
	'total_spent_gov_ind_inc_conservative_millions' : 'healthExpendGovIndConservativeMinusIncomeMillions',
	'total_spent_gov_ind_inc_millions' : 'healthExpendGovIndMinusIncomeMillions',
	'total_spent_gov_millions' : 'healthExpendGovMillions',
	'total_spent_pp_only_millions' : 'healthExpendMillions',
	'icer_gov_ind_inc_conservative_thousands_per_haly' : 'ICERhealthExpendGovIndConservativeMinusIncomeThousandsPerHaly',
	'icer_gov_ind_inc_thousands_per_haly' : 'ICERhealthExpendGovIndMinusIncomeThousandsPerHaly',
	'icer_gov_thousands_per_haly' : 'ICERhealthExpendGovThousandsPerHaly',
	'total_income_millions' : 'personIncomeMillions',
	'person_years' : 'personYears',
	
}

def MakeDiscountTable(name, outName, raw=False):
	toAppend = []
	for discount in [0, -0.03]:
		if raw:
			path = '{}/out_{}_year_year_0-114_discount_{}_raw.csv'.format(SOURCE, name, discount)
			df = pd.read_csv(path, index_col=list(range(3)), header=list(range(2)))
			df.columns.names = ['Scenario', 'Percentile']
			df = util.FilterOutMultiIndex(df, {'Sex' : 'All', 'strata' : 'All'})
			df = util.FilterOutMultiIndex(df.transpose(), {'Percentile' : '50%'}).transpose()
		else:
			path = '{}/out_{}_year_year_0-114_discount_{}.csv'.format(SOURCE, name, discount)
			df = pd.read_csv(path, index_col=list(range(3)))
			df = util.FilterOutMultiIndex(df, {'Sex' : 'All', 'strata' : 'All'})
		
		df = df[SCENE_MAP.keys()]
		df = df.rename(columns=SCENE_MAP)
		df.columns.name = 'Scenario'
		df = df.transpose()
		df = util.AddIndexLevel(df, 'Discount', '{:.0f}%'.format(-100*discount), toTopLevel=True)
		toAppend.append(df)
	df = pd.concat(toAppend)
	return df


def MakeStandardTable(name, outName):
	toAppend = []
	for raw in [False, True]:
		df = MakeDiscountTable(name, outName, raw=raw)
		df = util.AddIndexLevel(df, 'Raw Median', raw, toTopLevel=True)
		toAppend.append(df)
	df = pd.concat(toAppend)
	util.OutputToFile(df, 'output/{}'.format(outName))
	

for inName, outName in tablesToMake.items():
	MakeStandardTable(inName, outName)
				  