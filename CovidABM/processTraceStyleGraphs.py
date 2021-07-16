# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 12:28:02 2021

@author: wilsonte
"""

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
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
        
def PickOutIndexAndMetric(df, axis, metric, index, indexVals, bucketWidth=False, loglog=False):
    df = PickOutIndex(df, indexVals)
    
    splitNames = [x for x in index if x not in indexVals]
    #print(splitNames)
    #print(index)
    #print(indexVals)
    if bucketWidth:
        if loglog:
            print(df[axis])
            df[axis] = np.exp(np.floor(np.log(df[axis]) / bucketWidth) * bucketWidth)
            print(df[axis])
        else:
            df[axis] = np.floor(df[axis] / bucketWidth) * bucketWidth + bucketWidth/2
    # splitNames should only have one entry.
    df = df.set_index(['rand_seed', axis] + splitNames)
    df = df[[metric]]
    return df, splitNames[0]


def PlotIntegerRange(df, axis, metric, index, indexVals,
                     bar=False, doSum=False, doCount=False,
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
    
    
def PlotPartialStackedBar(df, axis, metric, index, indexVals, size=(9, 4.5), hlines=False,
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


def PlotRangeManyIndex(df, indexVals, axis, metric, bar=False, doSum=False, loglog=False,
                       doCount=False, hlines=False, bucketWidth=False, titlePrepend=''):
    for preset in indexVals:
        PlotIntegerRange(df, axis, metric, preset['ind'], preset['val'],
                         loglog=loglog,
                         bar=bar, doSum=doSum, doCount=doCount, hlines=hlines,
                         bucketWidth=bucketWidth, titlePrepend=titlePrepend)


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
        print(("Transmission >={}, #infections: {:.0f}, #runs {:.0f}, " + 
              "%infections: {:.01f}%, %runs: {:.01f}%").format(
            i, filterDf['incurR'].sum(), filterDf['incurR'].count(),
            100 * filterDf['incurR'].sum() / totalInfections,
            100 * filterDf['incurR'].count() / totalRuns))
    
    

def ProcessResults(nameList):
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
        'max_stage', 'param_policy',
        'stage1time', 'stage1btime', 
        'stage2time', 'stage3time', 'stage4time', 
        'casesinperiod7_min',
        'casesinperiod7_switchTime',
        'cumulativeInfected_switchTime',
    ]
    notFloatCol = ['param_policy']
    df = pd.DataFrame(columns=interestingColumns)
    for v in nameList:
        pdf = pd.read_csv(v + '.csv', header=6)
        pdf = pdf[interestingColumns]
        df  = df.append(pdf)
    
    for colName in interestingColumns:
        if colName not in notFloatCol:
            df[colName] = df[colName].astype(float)
    
    df = df.rename(columns={
        'first_trace_day' : 'first_report_day',
        'first_trace_occurred' : 'first_trace_occur',
        'isocomply_override' : 'IsoComply',
        'cali_symtomatic_present_day' : 'IncurPresentDay',
        'cali_asymptomaticFlag' : 'IncurAsymptomatic',
        'cali_timenow' : 'IncurDiseaseTime',
        'param_trace_mult' : 'TraceMult',
        'sympt_present_prop' : 'PresentProp',
        'cumulative_tracked_all' : 'culTrackAll',
        'cumulative_tracked_notice' : 'culNotice',
        'initial_infection_R' : 'incurR',
        'casesinperiod7_max' : 'maxCasesDailyOverWeek',
        'casesReportedToday_max' : 'maxCasesDaily',
        'casesinperiod7_switchTime' : 'intCasesWeekDaily',
    })
    
    df = df.set_index(['rand_seed', 'TraceMult', 'param_policy'])
    df['IncurPresentDay'] = df['IncurPresentDay'].replace(
        {-1 : 'None'})
    
    df['combinedStop'] = df.apply(lambda row:
        row['pre_stop_day'] if row['pre_stop_day'] > -1 else row['End_Day'], axis=1)
    
    
    df['maxCasesDailyOverWeek'] = df['maxCasesDailyOverWeek'] / 7
    df['intCasesWeekDaily'] = df['intCasesWeekDaily'] / 7
    df['culTrace'] = df['culTrackAll'] - df['culNotice']
    df['success'] = 0
    df.loc[df['casesinperiod7_min'] < 5, 'success'] = 1
    df['any_trace'] = 0
    df.loc[df['first_trace_occur'] >= 0, 'any_trace'] = 1
    df['any_transmit'] = 0
    df.loc[df['cumulativeInfected'] > 1, 'any_transmit'] = 1
    
    # Reset plot parameters
    dailyCaseLimit = 61
    plt.rcParams.update(plt.rcParamsDefault)
    df = df[df['maxCasesDailyOverWeek'] >= dailyCaseLimit]
    df = df.sort_index()
    print(df.index)
    
    if True:
        PlotIntegerRange(df, 'TraceMult', 'success',
                         ['TraceMult', 'param_policy'],
                         {'TraceMult' : 0.5},
                         bar=True, nameOverride='Success in runs with a week of at least {} average daily cases.'.format(dailyCaseLimit))
        indexList = [
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp', 'R0'], 
            # 'val' : {'TraceMult' : 1, 'PresentProp' : 0.5, 'R0' : 5}},
            {'ind' : ['TraceMult', 'param_policy'], 
             'val' : {'TraceMult' : 0.5}},
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp', 'R0'], 
            # 'val' : {'IsoComply' : 0.97, 'TraceMult' : 1, 'R0' : 2.5}},
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp', 'R0'], 
            # 'val' : {'IsoComply' : 0.97, 'TraceMult' : 1, 'R0' : 4.75}},
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp', 'R0'], 
            # 'val' : {'IsoComply' : 0.97, 'PresentProp' : 0.5, 'R0' : 2.5}},
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp', 'R0'], 
            # 'val' : {'IsoComply' : 0.97, 'PresentProp' : 0.5, 'R0' : 4.75}},
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp', 'R0'], 
            # 'val' : {'TraceMult' : 1, 'PresentProp' : 0.5, 'R0' : 2.5}},
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp', 'R0'], 
            # 'val' : {'TraceMult' : 1, 'PresentProp' : 0.5, 'R0' : 4.75}},
            #{'ind' : ['spread_deviate', 'move_deviate', 'virlce_deviate'], 
            # 'val' : {'move_deviate' : 1, 'virlce_deviate' : 1}},
            #{'ind' : ['spread_deviate', 'move_deviate', 'virlce_deviate'], 
            # 'val' : {'spread_deviate' : 1, 'move_deviate' : 1}},
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp', 'R0'], 
            # 'val' : {'TraceMult' : 1, 'PresentProp' : 0.5, 'IsoComply' : 0.97}},
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp'], 
            # 'val' : {'IsoComply' : 0.97, 'TraceMult' : 1}},
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp'], 
            # 'val' : {'IsoComply' : 0.97, 'PresentProp' : 0.5}},
            #{'ind' : ['IsoComply', 'TraceMult', 'PresentProp'], 
            # 'val' : {'TraceMult' : 2, 'PresentProp' : 0.65}},
        ]
        
        if True:
            #PlotStackedManyIndex(df, indexList, 'any_trace', 'success')
            #PlotRangeManyIndex(df[df['first_trace_occur'] >= 0], indexList, 'first_trace_occur', 'success')
            titlePrepend = '[min daily for week = {}] '.format(dailyCaseLimit)
            
            PlotRangeManyIndex(df, indexList, 'intCasesWeekDaily', 'success', doCount=True, bucketWidth=32/7, titlePrepend=titlePrepend)
            
            PlotRangeManyIndex(df, indexList, 'combinedStop', 'success', doCount=True, bucketWidth=5, titlePrepend=titlePrepend)
            PlotRangeManyIndex(df, indexList, 'cumulativeInfected', 'combinedStop', loglog=True, doCount=True, bucketWidth=1/15, titlePrepend=titlePrepend)
            
            #PlotRangeManyIndex(df, indexList, 'maxCasesDailyOverWeek', 'success', doCount=True, bucketWidth=25, titlePrepend=titlePrepend)
            #PlotRangeManyIndex(df, indexList, 'maxCasesDailyOverWeek', 'success', bucketWidth=25, titlePrepend=titlePrepend)
            PlotStackedManyIndex(df[df['maxCasesDailyOverWeek'] < 350], indexList, 'maxCasesDailyOverWeek', 'success', bucketWidth=20, titlePrepend=titlePrepend)
    
    print('Total runs {}'.format(df['combinedStop'].count()))
    for i in range(2, 5):
        print('Sucesse Rate max stage {} {}'.format(i, df.loc[(slice(None), slice(None), 'Stage{}'.format(i)),'success'].mean()))
    #PrintSomeStats(df, {'IsoComply' : 0.93, 'TraceMult' : 1, 'PresentProp' : 0.5})


def DoPreProcessChecks(subfolder):
    ProcessResults(util.GetFiles(subfolder + '/ABM_out/'))
    

