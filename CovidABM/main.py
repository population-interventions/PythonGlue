# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 12:16:11 2021

@author: wilsonte
"""


from processNetlogoOutput import DoAbmProcessing
from processNetlogoOutput import MakeHeatmaps
from processedOutputToPMSLT import DoProcessingForPMSLT

dataDir = '2021_03_31'

DoAbmProcessing(dataDir)
MakeHeatmaps(dataDir)
DoProcessingForPMSLT(dataDir)
