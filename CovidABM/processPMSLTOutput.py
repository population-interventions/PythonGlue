
import math
import pandas as pd
import numpy as np

from utilities import OutputToFile
from utilities import ToHeatmap


def HeatmapProcess(df):
    df = df.reset_index()
    df = df.drop(columns=['global_transmissibility'])

    df = ToHeatmap(df,
        ['param_policy', 'Var_R0_mult', 'R0', 'VacKids'],
        ['VacEfficacy', 'VacEff_VarMult', 'RolloutMonths'],
        sort_rows=[
            ['param_policy', {
                'ModerateSupress_No_4' : 'b',
                'ModerateSupress' : 'a',
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
                8 : 'a',
                12 : 'b',
                16 : 'c',
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


def ProcessPMSLTResults(dataDir, measureCols):
    processDir = dataDir + '/PMSLT_out/'
    reportDir = dataDir + '/Report_out/'
    
    df = pd.read_csv(processDir + 'PMSLT_out' + '.csv',
                     index_col=list(range(1 + len(measureCols))),
                     header=list(range(2)))
    
    df = df.unstack('RolloutMonths')
    df = df.reorder_levels([2, 1, 0], axis=1)
    df_vac = df.sub(df[0], axis=0) * -1
    
    df_vac = df_vac.reorder_levels([2, 1, 0], axis=1)
    df = df.reorder_levels([2, 1, 0], axis=1)
    
    OutputMedianUncertainTables(df, reportDir + 'process_describe', ['measure', 'period'])
    OutputMedianUncertainTables(df_vac, reportDir + 'process_describe_vacCompare', ['measure', 'period'])
