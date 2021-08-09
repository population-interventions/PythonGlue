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


def DoSpartanAggregate(dataDir, measureCols):
	AppendParallels(
		dataDir, '/ABM_process/', measureCols,
		'/outputs_post/step_1/', 'processed', 100, [
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
		dataDir, '/ABM_process/', measureCols,
		'/outputs_post/visualise/', 'processed', 100, [
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
	AppendParallels(
		dataDir, '/Mort_process/', measureCols,
		'/outputs_post/cohort/', 'infect', 100, [
			#'noVac', # Takes too long
			'noVac_daily',
			'noVac_weeklyAgg',
			'noVac_tendayAgg',
			'noVac_yearlyAgg',
			#'vac', # Takes too long
			'vac_daily',
			'vac_weeklyAgg',
			'vac_tendayAgg',
			'vac_yearlyAgg',
		],
	)
	
	AddFiles(dataDir + '/ABM_process/' + 'infect_unique_weeklyAgg',
		[
			dataDir + '/ABM_process/' + 'processed_infectNoVac_weeklyAgg',
			dataDir + '/ABM_process/' + 'processed_infectVac_weeklyAgg',
		],
		index=(2 + len(measureCols))
	)

