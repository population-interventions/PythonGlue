# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 12:28:02 2021

@author: wilsonte
"""

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
import matplotlib
import seaborn as sns
import pathlib
import utilities as util
#from tqdm import tqdm


def GetIndexPickStr(indexVals):
	lbl = "with"
	first = True
	for key in indexVals:
		if not first:
			lbl += ","
		lbl += " {} = {}".format(key, indexVals[key])
		first = False
	return lbl


def PickOutIndex(df, indexVals):
	df = df.reset_index()
	for key in indexVals:
		df = df[df[key] == indexVals[key]]
	return df


def PickOutIndexAndMetric(
		df, axis, metric, index, indexVals,
		bucketWidth=False, loglog=False):
	df = PickOutIndex(df, indexVals)
	
	splitNames = [x for x in index if x not in indexVals]
	#print(splitNames)
	#print(index)
	#print(indexVals)
	if bucketWidth:
		if loglog:
			df[axis] = np.exp(np.floor(np.log(df[axis]) / bucketWidth) * bucketWidth)
		else:
			df[axis] = np.floor(df[axis] / bucketWidth) * bucketWidth + bucketWidth/2
	# splitNames should only have one entry.
	df = df.set_index(['rand_seed', axis] + splitNames)
	df = df[[metric]]
	return df, splitNames[0]


def PrintMetrics(subfolder, df, axis, index, indexVals, name=False):
	df = PickOutIndex(df, indexVals)
	indexList = ['rand_seed'] + index
	df = df[indexList + [axis]].set_index(indexList)
	#print(df)
	util.PrintDuplicateRows(df.index.to_frame())
	df = df.unstack('rand_seed').transpose()
	df = df.describe(percentiles=[0.05,0.25,0.75,0.95])
	if not name:
		name = axis
	util.OutputToFile(df, subfolder + '/ABM_metrics/' + name, head=False)


def PrintMetricsManyIndex(subfolder, df, indexVals, axis, **kwargs):
	for preset in indexVals:
		PrintMetrics(subfolder, df, axis, preset['ind'], preset['val'], **kwargs)


def PlotViolin(
		df, axis, xSplit, indexVals,
		size=(9, 4.5), hlines=False, nameOverride=False,
		titlePrepend='', loglog=False, date=False, xlabels=False):
	print('PlotIntegerRange', axis, xSplit)
	df = PickOutIndex(df, indexVals)
	
	print('Plotting')
	#sns.set_palette("tab10")
	#sns.palplot(sns.color_palette("tab10"))
	palette = "muted"
	
	#print(df[[axis, xSplit]])
	if loglog:
		df[axis] = np.log10(df[axis])
	figure = sns.violinplot(x=xSplit, y=axis, data=df, linewidth=0.5,
							inner='quartile', scale='area', palette=palette,
							width=0.98, gridsize=200)
	if loglog:
		plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter("$10^{{{x:.0f}}}$"))
		
		lower = int(np.floor(figure.get_ylim()[0]))
		upper = int(np.ceil(figure.get_ylim()[1]))
		#print(lower, upper)
		
		plt.gca().yaxis.set_ticks([p for p in range(lower, upper)])
		plt.gca().yaxis.set_ticks([np.log10(x) for p in range(lower, upper) for x in np.linspace(10**p, 10**(p+1), 6)], minor=True)
	else:
		plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
		plt.gca().yaxis.set_minor_locator(ticker.AutoMinorLocator())
		
	plt.grid(which='major', axis='y')
	plt.grid(which='minor', axis='y', linewidth=0.2)
	plt.gca().set_axisbelow(True)
	
	if date:
		dateList = ["11$^{th}$ July '21", "1$^{st}$ Sep '21", "1$^{st}$ Nov '21",
					"1$^{st}$ Jan '22", "1$^{st}$ Mar '22", "1$^{st}$ May '22",
					"1$^{st}$ July '22"]
		#plt.yticks(rotation = 45)
		plt.gca().yaxis.set_ticks([0, 51, 112, 173, 234, 295, 356])
		plt.gca().yaxis.set_minor_locator(ticker.AutoMinorLocator())
		plt.gca().set_yticklabels(dateList)
		figure.set_ylim(0, 380)
		
	if xlabels:
		plt.gca().set_xticklabels(xlabels)
	
	for l in plt.gca().lines:
		l.set_linestyle('--')
		l.set_linewidth(0.9)
		l.set_color('black')
		l.set_alpha(0.6)
	for l in plt.gca().lines[1::3]:
		l.set_linestyle('-')
		l.set_linewidth(1)
		l.set_color('black')
		l.set_alpha(0.8)
	
	plt.gcf().set_size_inches(size[0], size[1])
	plt.xticks(rotation=0)
	plt.ylabel(axis)
	if not (loglog or date):
		figure.set_ylim(min(figure.get_ylim()[0], 0), max(figure.get_ylim()[1], 1))

	if nameOverride:
		figure.set_title(titlePrepend + nameOverride, fontsize=18)
	else:
		figure.set_title(titlePrepend + '{} by {} {}'.format(xSplit, axis, GetIndexPickStr(indexVals)))
	
	if hlines:
		for v in hlines:
			figure.axhline(y=v, linewidth=0.9, color='k', zorder=0, linestyle='--')
			plt.text(0.1, v + 8, '18$^{th}$ July - Restrictions applied', fontsize=8, rotation=0)
	
	plt.ylabel(None)
	plt.xlabel(None)
	plt.show()


def PlotIntegerRange(
		df, axis, metric, index, indexVals,
		bar=False, doSum=False, doCount=False, xlim=False,
		size=(9,4.5), hlines=False, nameOverride=False,
		bucketWidth=False, titlePrepend='', loglog=False):
	print('PlotIntegerRange', axis, metric)
	df, splitName = PickOutIndexAndMetric(df, axis, metric, index, indexVals, bucketWidth=bucketWidth, loglog=loglog)

	if doCount:
		df = df.groupby(level=[1, 2]).count()
	elif doSum:
		df = df.groupby(level=[1, 2]).sum()
	else:
		df = df.groupby(level=[1, 2]).mean()
	df = df.unstack(1)
	neighborhoods = list(dict.fromkeys(list(df.columns.get_level_values(1))))
	
	print('Plotting')
	if bar:
		figure = df.plot.bar(figsize=size, logx=loglog)
		plt.grid(which='major', axis='y')
		if not loglog:
			plt.grid(which='minor', linewidth=0.2, axis='y')
			if doCount or doSum:
				plt.gca().yaxis.set_minor_locator(ticker.AutoMinorLocator())
			else:
				plt.gca().yaxis.set_minor_locator(ticker.MultipleLocator(0.05))
		plt.gca().set_axisbelow(True)
	else:
		figure = df.plot(figsize=size, logx=loglog)
		plt.grid(which='major')
		plt.grid(which='minor', linewidth=0.2)
		if not loglog:
			plt.gca().xaxis.set_minor_locator(ticker.AutoMinorLocator())
			plt.gca().yaxis.set_minor_locator(ticker.AutoMinorLocator())
		
	plt.xticks(rotation=0)
	if doCount:
		plt.ylabel("number of runs")
	else:
		plt.ylabel(metric)
	figure.set_ylim(min(figure.get_ylim()[0], 0), max(figure.get_ylim()[1], 1))
	
	if xlim:
		figure.set_xlim(xlim[0], xlim[1])
	
	if nameOverride:
		figure.set_title(titlePrepend + nameOverride)
	elif doCount:
		figure.set_title(titlePrepend + 'runs by {} {}'.format(axis, GetIndexPickStr(indexVals)))
	else:
		figure.set_title(titlePrepend + '{} by {} {}'.format(metric, axis, GetIndexPickStr(indexVals)))
	
	plt.legend(neighborhoods, title=splitName)
	if hlines:
		for v in hlines:
			figure.axhline(y=v, linewidth=1, zorder=0, color='r')

	plt.show()


def PlotPartialStackedBar(
		df, axis, metric, index, indexVals, size=(9, 4.5), hlines=False,
		nameOverride=False, bucketWidth=False, titlePrepend=''):
	print('PlotPartialStackedBar', axis, metric)
	df, splitName = PickOutIndexAndMetric(df, axis, metric, index, indexVals, bucketWidth=bucketWidth)
	
	df['neg_' + metric] = 1 - df[metric]
	df = df.groupby(level=[1, 2]).sum()
	df = df.unstack(1)
	
	neighborhoods = list(dict.fromkeys(list(df.columns.get_level_values(1))))
	df = df.stack(0).reset_index()
	
	classes = list(dict.fromkeys(list(df[axis].values)))
	ind = np.arange(len(classes)) + .15
	fig, ax = plt.subplots()
	fig.set_size_inches(size[0], size[1])
	
	plt.grid(which='major', axis='y')
	plt.grid(which='minor', linewidth=0.2, axis='y')
	plt.gca().yaxis.set_major_locator(ticker.AutoLocator())
	plt.gca().yaxis.set_minor_locator(ticker.AutoMinorLocator())
	plt.gca().set_axisbelow(True)
	
	top_colors = ['#7EA3BC', '#FFB97C', '#9DE09D', '#E57072', '#BD98E0']
	bottom_colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD']
	width = 0.24
	print('Plotting')
	
	cur_width = 0
	for i, n in enumerate(neighborhoods):
		vis = df[(df.level_1 == metric)][n]
		non_vis = df[df.level_1 == 'neg_' + metric][n]
		rect1 = ax.bar(ind + cur_width, vis, float(width), color=bottom_colors[i])
		cur_width += 0.24
	
	cur_width = 0
	for i, n in enumerate(neighborhoods):
		vis = df[(df.level_1 == metric)][n]
		non_vis = df[df.level_1 == 'neg_' + metric][n]
		rect2 = ax.bar(ind + cur_width, non_vis, width, color=top_colors[i], bottom=vis)
		cur_width += 0.24
	
	extra_space = 0.205 - 0.225 * (5 - len(neighborhoods))/3
	ax.set_xticks(ind + width + extra_space)
	ax.set_xticklabels(classes)
	
	if nameOverride:
		ax.set_title(titlePrepend + nameOverride)
	else:
		ax.set_title(titlePrepend + '{} prop split by {} {}'.format(metric, axis, GetIndexPickStr(indexVals)))
	
	plt.xlabel(axis)
	plt.ylabel(metric)
	plt.legend(neighborhoods, title=splitName)
	if hlines:
		for v in hlines:
			ax.axhline(y=v, linewidth=1, zorder=0, color='r')
	plt.show()


def PlotRangeManyIndex(df, indexVals, axis, metric, **kwargs):
	for preset in indexVals:
		PlotIntegerRange(df, axis, metric, preset['ind'], preset['val'], **kwargs)


def PlotViolinManyIndex(df, indexVals, axis, xSplit, **kwargs):
	for preset in indexVals:
		PlotViolin(df, axis, xSplit, preset['val'], **kwargs)


def PlotStackedManyIndex(df, indexVals, axis, metric, bar=False, doSum=False,
						 doCount=False, hlines=False, bucketWidth=False, titlePrepend=''):
	for preset in indexVals:
		PlotPartialStackedBar(df, axis, metric, preset['ind'], preset['val'], hlines=hlines,
							  bucketWidth=bucketWidth, titlePrepend=titlePrepend)


def PrintSomeStats(df, indexVals):
	df = PickOutIndex(df, indexVals)
	
	totalInfections = df['incurR'].sum()
	totalRuns = len(df['any_transmit'])
	noTransmitProp = len(df[df['any_transmit'] == 0]) / totalRuns
	
	print('=== Stats {} ==='.format(GetIndexPickStr(indexVals)))
	print("Runs with no transmission", noTransmitProp)
	print("Total Infections: {}, Total runs: {}".format(totalInfections, totalRuns))
	for i in range(1,16):
		filterDf = df[df['incurR'] >= i]
		print((
			"Transmission >={}, #infections: {:.0f}, #runs {:.0f}, " + 
			"%infections: {:.01f}%, %runs: {:.01f}%").format(
				i, filterDf['incurR'].sum(), filterDf['incurR'].count(),
				100 * filterDf['incurR'].sum() / totalInfections,
				100 * filterDf['incurR'].count() / totalRuns))


def ProcessResults(
		subfolder, indexRenameFunc, measureCols, measureCols_raw,
		defaultValues, nameList):
	name = nameList[0]
	interestingColumns = [
		'param_trace_mult', 'sympt_present_prop',
		'rand_seed', 'isocomply_override', 'End_Day', 'pre_stop_day',
		'infectionsToday', 'first_trace_day', 'first_trace_infections',
		'currentInfections', 'cumulativeInfected', 'tracked_simuls',
		'finished_infections', 'finished_tracked',
		'cali_timenow', 'cali_asymptomaticFlag',
		'cali_symtomatic_present_day',
		'first_trace_occurred', 'cumulative_tracked_all',
		'cumulative_tracked_notice', 'initial_infection_R',
		'casesinperiod7_max', 'casesReportedToday_max',
		'max_stage',
		'stage1time', 'stage1btime', 
		'stage2time', 'stage3time', 'stage4time', 
		'casesinperiod7_min',
		'casesinperiod7_switchTime',
		'cumulativeInfected_switchTime',
		'initial_cases',
	] + measureCols_raw
	
	df = pd.DataFrame(columns=interestingColumns)
	for v in nameList:
		pdf = pd.read_csv(v + '.csv', header=6)
		pdf = pdf[interestingColumns]
		df  = df.append(pdf)
	
	for colName in interestingColumns:
		#print(df[colName].head(1)[0])
		if colName and util.isfloat(df[colName].head(1)[0]):
			df[colName] = df[colName].astype(float)
	
	df = df.rename(columns={
		'first_trace_day' : 'first_report_day',
		'first_trace_occurred' : 'first_trace_occur',
		'isocomply_override' : 'IsoComply',
		'cali_symtomatic_present_day' : 'IncurPresentDay',
		'cali_asymptomaticFlag' : 'IncurAsymptomatic',
		'cali_timenow' : 'IncurDiseaseTime',
		'sympt_present_prop' : 'PresentProp',
		'cumulative_tracked_all' : 'culTrackAll',
		'cumulative_tracked_notice' : 'culNotice',
		'initial_infection_R' : 'incurR',
		'casesinperiod7_max' : 'maxCasesDailyOverWeek',
		'casesReportedToday_max' : 'maxCasesDaily',
		'casesinperiod7_switchTime' : 'intCasesWeekDaily',
	})
	
	df = df.set_index(['rand_seed'] + measureCols_raw)
	df = indexRenameFunc(df)
	
	df['IncurPresentDay'] = df['IncurPresentDay'].replace(
		{-1 : 'None'})
	
	df['combinedStop'] = df.apply(lambda row:
		row['pre_stop_day'] if row['pre_stop_day'] > -1 else row['End_Day'], axis=1)
	
	df['cumulativeInfected'] = df['cumulativeInfected'] - df['initial_cases']
	
	df['maxCasesDailyOverWeek'] = df['maxCasesDailyOverWeek'] / 7
	df['intCasesWeekDaily'] = df['intCasesWeekDaily'] / 7
	df['culTrace'] = df['culTrackAll'] - df['culNotice']
	df['success'] = 0
	df.loc[df['pre_stop_day'] > -1, 'success'] = 1
	df['any_trace'] = 0
	df.loc[df['first_trace_occur'] >= 0, 'any_trace'] = 1
	df['any_transmit'] = 0
	df.loc[df['cumulativeInfected'] > 1, 'any_transmit'] = 1
	
	# Reset plot parameters
	dailyCaseLimit = 0
	plt.rcParams.update(plt.rcParamsDefault)
	
	df = df[df['maxCasesDailyOverWeek'] >= 5]
	df = df.sort_index()
	
	fullIndex = measureCols
	
	if True:
		#PlotIntegerRange(df, 'TraceMult', 'success',
		#                 ['TraceMult', 'param_policy'],
		#                 {'TraceMult' : 1},
		#                 bar=True,
		#                 nameOverride='Success in runs with a week of at least {} average daily cases.'.format(dailyCaseLimit))
		
		metricList = [
			{
				'ind' : fullIndex, 
				'val' : {}
			},
		]
		
		indexList = []
		for valueDict in defaultValues:
			for key, value in valueDict.items():
				newPlot = {
					'ind' : fullIndex, 
					'val' : { k : v for (k, v) in valueDict.items() if k != key},
				}
				indexList.append(newPlot)
		
		if True:
			#PlotStackedManyIndex(df, indexList, 'any_trace', 'success')
			#PlotRangeManyIndex(df[df['first_trace_occur'] >= 0], indexList, 'first_trace_occur', 'success')
			titlePrepend = '[min daily for week = {}] '.format(dailyCaseLimit)
			
			PrintMetricsManyIndex(subfolder, df, metricList, 'combinedStop')
			PrintMetricsManyIndex(subfolder, df, metricList, 'cumulativeInfected')
			
			#PlotRangeManyIndex(df, indexList, 'intCasesWeekDaily', 'success', doCount=True, bucketWidth=32/7, titlePrepend=titlePrepend)
			PlotRangeManyIndex(df, indexList, 'combinedStop', 'success', doCount=True, bucketWidth=5)
			PlotRangeManyIndex(df, indexList, 'cumulativeInfected', 'combinedStop', loglog=True, doCount=True, bucketWidth=1/15)
			
			#PlotViolinManyIndex(df, indexList, 
			#                    'intCasesWeekDaily', 
			#                    'param_policy',
			#                    nameOverride='Daily cases over the week prior to lockdown',
			#                    )
			#PlotViolinManyIndex(df,
			#                    indexList, 'combinedStop', 
			#                    'param_policy', 
			#                    hlines=[14], date=True,
			#                    xlabels=['Stage 2', 'Stage 3', 'Stage 4'],
			#                    nameOverride='Expected date of five daily cases',
			#                    )
			#PlotViolinManyIndex(df, indexList,
			#                    'cumulativeInfected', 
			#                    'param_policy', loglog=True,
			#                    xlabels=['Stage 2', 'Stage 3', 'Stage 4'],
			#                    nameOverride='Expected infections prior to reaching five daily cases',
			#                    )
			
			#PlotRangeManyIndex(df, indexList, 'maxCasesDailyOverWeek', 'success', doCount=True, bucketWidth=25, titlePrepend=titlePrepend)
			#PlotRangeManyIndex(df, indexList, 'maxCasesDailyOverWeek', 'success', bucketWidth=25, titlePrepend=titlePrepend)
			#PlotStackedManyIndex(df[df['maxCasesDailyOverWeek'] < 350], indexList, 'maxCasesDailyOverWeek', 'success', bucketWidth=20, titlePrepend=titlePrepend)

	print('Total runs {}'.format(df['combinedStop'].count()))
	#for i in range(2, 5):
	#    print('Sucesse Rate max stage {} {}'.format(i, df.loc[(slice(None), slice(None), 'Stage{}'.format(i)),'success'].mean()))
	#PrintSomeStats(df, {'IsoComply' : 0.93, 'TraceMult' : 1, 'PresentProp' : 0.5})


def DoPreProcessChecks(
		subfolder, rawDataDir, indexRenameFunc, measureCols, measureCols_raw,
		defaultValues, firstOnly=False):
	ProcessResults(
		subfolder, indexRenameFunc, measureCols, measureCols_raw,
		defaultValues,
		util.GetFiles(rawDataDir, firstOnly=firstOnly))
