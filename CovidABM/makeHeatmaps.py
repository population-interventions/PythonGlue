
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
    

def MakeInfectionHeatmap(name, aggType, outputFile, inputFile, measureCols, startWeek=13, window=26):
    
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(4 + len(measureCols))),
                     header=list(range(1)))
    df = df.groupby(level=list(range(2, 4 + len(measureCols))), axis=0).mean()
    # Do (startWeek + 1) because week 0 consists of a single day, day 0.
    df = df[[str(i + startWeek + 1) + '.0' for i in range(window)]]
    df = df.transpose().describe().transpose()
    df = df[[aggType]] / 7
    df = df.rename(columns={aggType: name})
    
    df = HeatmapProcess(df)
    OutputToFile(df, outputFile)
    

def MakeStagesHeatmap(name, aggType, outputFile, inputFile, measureCols, startWeek=13, window=26):
    df = pd.read_csv(inputFile + '.csv',
                     index_col=list(range(4 + len(measureCols))),
                     header=list(range(3)))
    df = df.apply(lambda c: [1 if x > 2 else 0 for x in c])
    df = df.groupby(level=list(range(2, 4 + len(measureCols))), axis=0).mean()
    
    df = df.droplevel([0, 2], axis=1)
    # Add 1 to the day because week 0 consists of a single day, day 0.
    df = df[[str(i + startWeek*7 + 1) for i in range(window*7)]]
    df = df.transpose().describe().transpose()
    df = df[[aggType]]
    df = df.rename(columns={aggType : name})
    
    df = HeatmapProcess(df)
    OutputToFile(df, outputFile)


def MakeHeatmaps(dataDir, measureCols):
    processDir = dataDir + '/ABM_process/'
    visualDir = dataDir + '/ABM_heatmaps/'
    aggType = 'mean'
    
    print('Processing MakeInfectionHeatmap full')
    MakeInfectionHeatmap('full', aggType,
                         visualDir + 'infect_average_daily_full',
                         processDir + 'infect_unique_weeklyAgg',
                         measureCols,
                         startWeek=0, window=104)
    print('Processing MakeStagesHeatmap stage full')
    MakeStagesHeatmap('full', aggType,
                      visualDir + 'lockdown_proportion_full',
                      processDir + 'processed_stage',
                      measureCols,
                      startWeek=0, window=104)
    
    start = 0
    for i in range(4):
        print('Processing ' + str(start) + '_to_' + str(start + 26))
        MakeInfectionHeatmap(str(start) + '_to_' + str(start + 26), aggType,
                             visualDir + 'infect_average_daily_' + str(start) + '_to_' + str(start + 26),
                             processDir + 'infect_unique_weeklyAgg',
                             measureCols,
                             startWeek=start, window=26)
        MakeStagesHeatmap(str(start) + '_to_' + str(start + 26), aggType,
                          visualDir + 'lockdown_proportion_' + str(start) + '_to_' + str(start + 26),
                          processDir + 'processed_stage',
                          measureCols,
                          startWeek=start, window=26)
        start = start + 26
