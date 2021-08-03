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
from utilities import AddFiles
from utilities import ToHeatmap


def SumDir(dataDir, outputSubdir, prefix, arrayIndex, fileNames):
	for file in fileNames:
		print('\n' + file)
		AddFiles(
			dataDir + '/ABM_out/' + prefix + '_' + file,
			[dataDir + outputSubdir + '_' + file + '_' + str(x + 1) for x in range(arrayIndex)],
			doTqdm=True,
		)


def DoSpartanAggregate(dataDir, measureCols):
	SumDir(dataDir, '/outputs_post/step_1/process', 'processed', 100, [
		'case',
		'case7',
		'case14',
		#'infectNoVac',
		#'infectVac',
		'stage',
		
	],)
	SumDir(dataDir, '/outputs_post/visualise/', 'processed', 100, [
		'case_daily',
		'case_weeklyAgg',
		'case7_daily',
		'case7_weeklyAgg',
		'case14_daily',
		'case14_weeklyAgg',
		'infectNoVac_weeklyAgg',
		'infectVac_weeklyAgg',
		'stage_weeklyAgg',
		
	],)
	
	AddFiles(dataDir + '/ABM_process/' + 'infect_unique_weeklyAgg',
		[
			dataDir + '/ABM_process/' + 'processed_infectNoVac_weeklyAgg',
			dataDir + '/ABM_process/' + 'processed_infectVac_weeklyAgg',
		],
		index=(2 + len(measureCols))
	)

