
import source.include.utilities as util

envName = 'Unknown'
scenarioName = 'Unknown'

def SetEnv(name):
	global envName
	envName = name


def ResetEnv():
	global envName
	envName = 'Unknown'


def SetScenario(name):
	global scenarioName
	scenarioName = name
	

def ResetScenario():
	global scenarioName
	scenarioName = 'Unknown'


def PrintSemanticTrace():
	util.CondPrint('=======================================================================')
	util.CondPrint('Trace: Error in scenario [{}] and environment [{}].'.format(scenarioName, envName))
	util.CondPrint('=======================================================================')
