# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 10:22:33 2021

@author: wilsonte
"""

import math
import pandas as pd
import numpy as np
from tqdm import tqdm
import pathlib
import time
import os

from utilities import SplitNetlogoList
from utilities import SplitNetlogoNestedList
from utilities import OutputToFile
from utilities import AddFiles, AppendFiles
from utilities import ToHeatmap


def AppendParallels(dataDir, outDir, measureCols, outputSubdir, prefix, arrayIndex, fileNames, header=1):
	for file in fileNames:
		print('\n' + file)
		AppendFiles(
			dataDir + outDir + prefix + '_' + file,
			[dataDir + outputSubdir + prefix + '_' + file + '_' + str(x + 1) for x in range(arrayIndex)],
			doTqdm=True,
			index=len(measureCols) + 2,
			header=header,
		)


def DoSpartanAggregate(dataDir, measureCols, arraySize=100, doTenday=False, doLong=False):
	mortAgg = [
		'noVac_daily',
		'noVac_weeklyAgg',
		'noVac_yearlyAgg',
		'vac_daily',
		'vac_weeklyAgg',
		'vac_yearlyAgg',
	]
	
	if doTenday:
		mortAgg = mortAgg + [
			'noVac_tendayAgg',
			'vac_tendayAgg',
		]
	
	if doLong:
		# May not exist as these files are large.
		mortAgg = mortAgg + [
			'noVac',
			'vac',
		]
	
	AppendParallels(
		dataDir, '/Mort_process/', measureCols,
		'/outputs_post/cohort/', 'infect', arraySize, mortAgg)
	
	AppendParallels(
		dataDir, '/Traces/', measureCols,
		'/outputs_post/step_1/', 'processed', arraySize, [
			'case',
			'case7',
			'case14',
			#'infectNoVac', # Takes too long
			#'infectVac', # Takes too long
			'stage',
		],
		header=3,
	)
	
	AppendParallels(
		dataDir, '/Traces/', measureCols,
		'/outputs_post/visualise/', 'processed', arraySize, [
			'case_daily',
			'case_weeklyAgg',
			'case7_daily',
			'case7_weeklyAgg',
			'case14_daily',
			'case14_weeklyAgg',
			'infectNoVac_weeklyAgg',
			'infectVac_weeklyAgg',
			'stage_weeklyAgg',
		],
	)
	
	AddFiles(dataDir + '/Traces/' + 'infect_unique_weeklyAgg',
		[
			dataDir + '/Traces/' + 'processed_infectNoVac_weeklyAgg',
			dataDir + '/Traces/' + 'processed_infectVac_weeklyAgg',
		],
		index=(2 + len(measureCols))
	)

