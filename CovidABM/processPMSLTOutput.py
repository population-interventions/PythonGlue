
import math
import pandas as pd
import numpy as np

from utilities import OutputToFile
from utilities import ToHeatmap


def HeatmapProcess(df):
    df.index = df.index.droplevel('measure')
    df = df.reset_index()
    
    df = ToHeatmap(df,
        ['param_policy', 'Var_R0_mult', 'R0', 'VacKids'],
        ['VacEfficacy', 'VacEff_VarMult', 'RolloutMonths'],
        sort_rows=[
            ['param_policy', {
                'Stage2' : 'b',
                'Stage2b' : 'a',
            }],
            ['Var_R0_mult', {
                1.3 : 'a',
                1.45 : 'b',
                1.6 : 'c',
            }],
            ['R0', {
                2.5 : 'a',
                3 : 'b',
            }],
            ['VacKids', {
                'Yes' : 'a',
                'No' : 'b',
            }],
        ], 
        sort_cols=[
            ['VacEfficacy', {
                0.75 : 'c',
                0.875 : 'b',
                0.95 : 'a',
            }],
            ['VacEff_VarMult', {
                0.8 : 'b',
                0.95 : 'a',
            }],
            ['RolloutMonths', {
                0 : 'a',
                8 : 'b',
                12 : 'c',
                16 : 'd',
            }],
        ]
    )
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
    stageDf = pd.read_csv(stageFile + '.csv', 
                             index_col=list(range(1 + len(measureCols))),
                             header=[0, 1])
    
    stageDf = stageDf.transpose().reorder_levels([1, 0], axis=0).unstack('year') * 365 / 7
    stageDf = stageDf.mul(gdp_effects['gdpPerWeek'], axis=0).transpose()
    stageDf = stageDf.unstack(['RolloutMonths']).groupby(level=[1], axis=1).sum()
    stageDf = stageDf.unstack('year').reorder_levels([1, 0], axis=1)
    stageDf = stageDf['0'] + stageDf['1']
    return stageDf
    
    
def ProcessHealthPerspective(df, reportDir, subfolder, measureCols, addGDP=False):
    df = df['life']
    df_HALY = df['HALY']
    df_HALY = df_HALY.sub(df_HALY[0.0], axis=0) * -1
    df_spent = df['spent']
    df_spent = df_spent.sub(df_spent[0.0], axis=0)
    df_spent_12b = df_spent
    
    gdpCost = ProcessGDP(subfolder, measureCols)
    gdpCost = gdpCost.sub(gdpCost[0.0], axis=0)
    #print(gdpCost[12])
    #print((df_spent[12] + 1.2 * 10**9))
    #print(df_HALY[12])
    df_ICER = (df_spent[12] + 1.2 * 10**9 + gdpCost[12]) / df_HALY[12]
    #print(df_column_one)
    
    df_spend_to_8 = 1300 * (df_HALY[12] - df_HALY[8]) - (df_spent[12] - df_spent[8])
    print(df_column_two)
    

def ProcessPMSLTResults(dataDir, measureCols):
    processDir = dataDir + '/PMSLT_out/'
    reportDir = dataDir + '/Report_out/'
    
    df = pd.read_csv(processDir + 'PMSLT_out' + '.csv',
                     index_col=list(range(1 + len(measureCols))),
                     header=list(range(2)))
    
    OutputToFile(HeatmapProcess(df[[['life', 'deaths']]].stack('measure')), dataDir + '/PMSLT_heatmaps/deaths')
    
    df = df.unstack('RolloutMonths')
    df = df.reorder_levels([2, 1, 0], axis=1)
    df_vac = df.sub(df[0], axis=0) * -1
    
    df_vac = df_vac.reorder_levels([2, 1, 0], axis=1)
    df = df.reorder_levels([2, 1, 0], axis=1)
    
    ProcessHealthPerspective(df, reportDir, dataDir, measureCols)
    
    OutputMedianUncertainTables(df, reportDir + 'process_describe', ['measure', 'period'])
    OutputMedianUncertainTables(df_vac, reportDir + 'process_describe_vacCompare', ['measure', 'period'])
