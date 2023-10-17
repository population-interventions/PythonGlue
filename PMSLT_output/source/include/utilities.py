import pandas as pd
import numpy as np
import scipy
import math
import pdb
import shutil
import cProfile
import pstats
import io
import os
import json
import tqdm
import sys
import itertools

import matplotlib.pyplot as plt

from pathlib import Path
import importlib
import copy

import source.include.errorTrace as trace

from datetime import datetime, timezone
import subprocess

fileCreated = {}
pyPathFixApplied = False
HEAD_MODE = True
printEnabled = True

def SetAllowPrint(newAllowed):
	global printEnabled
	printEnabled = newAllowed


def CondPrint(*args):
	if printEnabled:
		print(*args)


def CondTqdm(*args, **kwargs):
	if printEnabled:
		return tqdm.tqdm(*args, **kwargs)
	return args[0]


def GetGitTimeIdentifier():
	now = datetime.now()
	dateString = now.strftime('%Y-%m-%dT%H_%M_%S')
	shortHash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
	return '{}_g{}'.format(dateString, shortHash)


def WriteToFile(data, path):
	#CondPrint('Writing to', path)
	MakePath(path)
	with open(path + '.txt', 'w') as f:
		f.write(data)


def WriteListToFile(path, data, addNewline=True):
	#CondPrint('Writing to', path)
	MakePath(path)
	with open(path + '.txt', 'w') as f:
		for line in data:
			f.write(line)
			if addNewline:
				f.write('\n')


def CopyDirectory(source, dest):
	MakePath(dest)
	if os.path.exists('{}'.format(source)) and os.path.exists('{}'.format(dest)):
		CondPrint('Copying {} to {}'.format(source, dest))
		shutil.copytree(
			'{}'.format(source),
			'{}'.format(dest),
			dirs_exist_ok=True
		)
	else:
		CondPrint('WARNING MISSILE DIRECTORY {}'.format(source))


def CopyFile(source, dest):
	MakePath(dest)
	if os.path.isfile('{}'.format(source)):
		CondPrint('Copying {} to {}'.format(source, dest))
		shutil.copyfile(
			'{}'.format(source),
			'{}'.format(dest)
		)
	else:
		CondPrint('WARNING MISSILE FILE {}'.format(source))


def WriteRunIdFile(path, identifier):
	WriteListToFile(path, [identifier], addNewline=False)


def PathExists(path):
	return os.path.exists(path)


def LoadJson(filePath):
	with open('{}.json'.format(filePath)) as json_file:
		try:
			return json.load(json_file)
		except ValueError as err:
			CondPrint("=== Json Error ===")
			CondPrint("File: '{}.json'".format(filePath))
			CondPrint(err)
			CondPrint(json_file.read())
			return False


def StringToFile(string, path):
	MakePath(path)
	with open(path, 'w') as outfile:
		outfile.write(string)


def WriteJsonFile(data, path, pretty=True):
	path = path + '.json'
	if pretty:
		StringToFile(json.dumps(data, indent=4), path)
	else:
		StringToFile(json.dumps(data), path)


def LoadMultiDirectoryJson(dirList, fileName, allowFailure=False):
	for path in dirList:
		fullPath = '{}/{}.json'.format(path, fileName)
		if PathExists(fullPath):
			return LoadJson('{}/{}'.format(path, fileName))
	if allowFailure:
		return False
	raise ValueError('Cannot find json file {} with paths {}.'.format(fileName, dirList))


def get_data_dir(population):
	here = Path(__file__).resolve()
	return here.parent / 'artifacts' / population


def LoadFunction(function_string):
	#global pyPathFixApplied
	#if not pyPathFixApplied:
	#	# Tell the module loader to always check the current path.
	#	CondPrint('sys.path', sys.path)
	#	if '' not in sys.path:
	#		sys.path.insert(0, '')
	#	pyPathFixApplied = True
	
	newPath = False
	if function_string.find('...') > -1:
		oldWorkingDir = os.getcwd()
		newWorkDir = oldWorkingDir.replace('/', '.').replace('\\', '.')
		while function_string[:3] == '...':
			function_string = function_string[3:]
			lastDot = newWorkDir.rfind('.')
			newWorkDir = newWorkDir[:lastDot]
		#os.chdir(newWorkDir.replace('.', '/'))
		
		filePath, func_name = function_string.rsplit('.', 1)
		mod_path, mod_name = filePath.rsplit('.', 1)
		newPath = '{}/{}'.format(newWorkDir, mod_path).replace('.', '/')
		if newPath in sys.path:
			sys.path.remove(newPath)
		sys.path.insert(0, newPath)
	else:
		mod_name, func_name = function_string.rsplit('.', 1)
	
	mod = importlib.import_module(mod_name)
	func = getattr(mod, func_name)
	
	if (newPath is not False) and (newPath in sys.path):
		sys.path.remove(newPath)
	return func


def ListDirPaths(path, addPath=False, recursive=False, removeExtension=True):
	if not os.path.exists(path):
		return []
	if not recursive:
		fileList = os.listdir(path)
		if addPath:
			fileList = ['{}/{}'.format(path, x) for x in fileList]
	else:
		fileList = []
		for root, subFolders, files in os.walk(path):
			root = root.replace('\\', '/')
			if not addPath:
				root = root[len(path) + 1:]
			for fileName in files:
				fileList.append('{}/{}'.format(root, fileName))
		
	if removeExtension:
		fileList = [(x[:x.rfind('.')] if x.rfind('/') < x.rfind('.') else x) for x in fileList]
	return fileList


def GetFigMult(x, sigFigs):
	return 10**math.floor(math.log10(abs(x)) - sigFigs + 1)


def RoundNumber(x, sigFigs):
	if x == np.inf:
		return 'Infinity'
	if x ==- np.inf:
		return '-Infinity'
	if np.isnan(x):
		return 'NaN'
	
	if abs(x) > 10**sigFigs:
		return '{:,.0f}'.format(GetFigMult(x, sigFigs)*round(x/GetFigMult(x, sigFigs)))
	
	numStr = '{:.{}e}'.format(x, sigFigs)
	if 'e' not in numStr:
		return numStr
	mantissa, exponent = numStr.split('e')
	mantissa = float(mantissa)
	exponent = int(exponent)
	return '{:,.{}f}'.format(x, max(0, sigFigs - exponent - 1))


def PrettyRoundDf(df, sigFigs, divisor=1):
	df = df / divisor
	df = df.applymap(lambda x: RoundNumber(x, sigFigs))
	return df


def CubicSpline(x, lower, mid, upper):
	return (1 - x) * ((1 - x) * lower + x * mid) + x * ((1 - x) * mid + x * upper)


def PrToLogOdds(x, safe=False):
	if safe:
		# Don't use these values, just put them here to prevent
		# errors in intermediate processing.
		x = np.clip(x, 0.0000000001, 0.9999999999)
	return np.log(x/(1 - x))


def LogOddsToPr(x):
	return np.exp(x)/(1 + np.exp(x))


def UnstackDraw(df):
	df = df.sort_values(['year_start', 'age_start', 'sex', 'strata', 'draw'])
	df = df.set_index(['year_start',  'year_end', 'age_start', 'age_end', 'sex', 'strata', 'draw'])
	df = df.unstack(level='draw')
	df = df.droplevel(0, axis=1)
	col_frame = df.columns.to_frame()
	col_frame = col_frame.reset_index(drop=True)
	col_frame['draw'] = 'draw_' + col_frame['draw'].astype(str)
	df.columns = pd.Index(col_frame['draw'])
	df.columns.name = None
	df = df.reset_index()
	return df


def CrossDf(df1, df2):
	return (df1
		.assign(_cross_merge_key=1)
		.merge(df2.assign(_cross_merge_key=1), on="_cross_merge_key")
		.drop("_cross_merge_key", axis=1)
	)


def PrintDuplicateRows(df):
	df = df[df.duplicated()]
	CondPrint(df)


def HasDuplicateRows(df):
	df = df[df.duplicated()]
	return not df.empty


def GetDuplicateRows(df, groupCols=False):
	if groupCols is not False:
		grouped = df.groupby(groupCols, as_index=False)
	else:
		grouped = df.groupby(df.columns.tolist(), as_index=False)
	list_of_lists = ([
		value for key, value in grouped.groups.items()
	])
	return list_of_lists


def PrintDuplicateIndex(df):
	CondPrint("PrintDuplicateIndex")
	CondPrint(PrintDuplicateRows(df.index.to_frame()))


def PrintMultiIndexValues(df):
	levels = df.index.levels
	CondPrint('=== PrintMultiIndexValues ===')
	expectedSize = 1
	for level_num, level in enumerate(levels):
		CondPrint('Level {} {}: {}'.format(
			level_num + 1,
			level.name,
			level.tolist()
		))
		expectedSize = expectedSize * len(level.tolist())
	CondPrint(df)
	CondPrint('Expected index size: {}'.format(expectedSize))
	PrintDuplicateIndex(df)


def HasDuplicateIndex(df):
	df = df.index.duplicated()
	return (True in df)


def ToSeries(df):
	if isinstance(df, pd.Series):
		return df
	return df[df.columns[0]]


def MakePath(path):
	if '/' not in path:
		return
	out_folder = os.path.dirname(path)
	if not os.path.exists(out_folder):
		MakePath(out_folder)
		os.makedirs(out_folder, exist_ok=True)


def ResetFileCreationCache():
	global fileCreated
	fileCreated = {}


def OutputToFile(df, path, index=True, head=False, replace=False):
	# Write dataframe to a file.
	# Appends dataframe when called with the same name.
	fullFilePath = path + '.csv'
	MakePath(path)
	if fileCreated.get(fullFilePath) and not replace:
		# Append
		df.to_csv(fullFilePath, mode='a', header=False, index=index)
	else:
		fileCreated[fullFilePath] = True
		df.to_csv(fullFilePath, index=index)
		if HEAD_MODE and head:
			last = path.rfind('/')
			df.head(100).to_csv(path[:last + 1] + '_head_' + path[last + 1:] + '.csv', index=index) 


def OutputRawRowsToFile(rows, path):
	# Write dataframe to a file.
	# Appends dataframe when called with the same name.
	fullFilePath = path + '.txt'
	MakePath(path)
	with open(fullFilePath, 'w') as f:
		for row in rows:
			f.write('\t'.join(row) + '\n')


def CleanCsv(df):
	if 'year_end' in df.columns:
		df = df.drop(columns=['year_end'])
	return df


def LoadCleanCsv(fileName, index_col=False):
	if index_col is not False:
		df = pd.read_csv(
			fileName + '.csv', index_col=index_col,
			dtype={
				'year_start' : 'int64',
				'year_end' : 'int64',
				'age' : 'int64',})
	else:
		df = pd.read_csv(
			fileName + '.csv',
			dtype={
				'year_start' : 'int64',
				'year_end' : 'int64',
				'age' : 'int64',})
	return CleanCsv(df)


def CheckDf(df, msg='', length=False):
	if df.isnull().values.any():
		CondPrint('df found with nan entries')
		trace.PrintSemanticTrace()
		CondPrint(msg)
		CondPrint(df)
		raise ValueError('df found with nan entries')
	if length is not False and len(df) != length:
		CondPrint('df found with length {}, expected {}'.format(len(df), length))
		CondPrint(msg)
		CondPrint(df)
		trace.PrintSemanticTrace()
		raise ValueError('df length error')


def RaiseProblemsWithNumericDataFrame(df, name):
	types = df.dtypes
	if str in types or object in types:
		raise ValueError('Error with file {}. It contains non-numeric types.'.format(name))
	if df.isnull().values.any():
		raise ValueError('Error with file {}. It contains NaN values.'.format(name))


def CheckStatePropTable(df, fix=True, crash=False, warn=True):
	if not (fix or crash or warn):
		return df
	
	dfSum = df.sum(axis=1)
	if fix:
		df = df.divide(dfSum, axis=0)
	
	if ((dfSum > 1.000001) | (dfSum < 0.999999)).any():
		if warn:
			CondPrint(df)
			CondPrint(df[(dfSum > 1.000001) | (dfSum < 0.999999)])
			CondPrint("warning: State value sum not equal to 1.")
		if crash:
			trace.PrintSemanticTrace()
			raise ValueError("State dataframe sum error")
	return df


def ExtendIndexToMatch(df, newIndex):
	## The index of df must be a subset of newIndex, both in terms of
	## levels and rows.
	## Adds levels to the index of df, duplicating the rows that correspond
	## to the previous index.
	## Outputs a df with index newIndex.
	toMatch = newIndex.to_frame().reset_index(drop=True)
	toMatch = toMatch.set_index(df.index.names)
	df = df.join(toMatch, on=df.index.names).dropna()
	df = df.reset_index().set_index(newIndex.names).sort_index()
	return df


def SetStandardIndex(df):
	# Sorts age sex strata.
	if df.index.names != [None]:
		df = df.reset_index()
	toSet = ['year_of_birth', 'year_start', 'year', 'year_range', 'age', 'sex', 'strata', 'agecategory']
	# Do this rather than (set & set) to control order
	for x in toSet.copy():
		if x not in df.columns:
			toSet.remove(x)
	if len(toSet) == 0:
		return df
	df = df.set_index(toSet).sort_index()
	return df


def AddYearOfBirth(df):
	index = df.index.to_frame()
	index['year_of_birth'] = index['year'] - index['age']
	df.index = pd.MultiIndex.from_frame(index)
	return df


def ListIntersection(list_1, list_2):
	# Maintain order of list 1
	listOut = []
	for x in list_1:
		if x in list_2:
			listOut.append(x)
	return listOut


def ListRemove(myList, element, elementIsList=False):
	# Use elementIsList=True to remove a single element that happens to
	# be a list, rather than to remove a list of elements.
	if type(element) == list and not elementIsList:
		for e in element:
			myList = ListRemove(myList, e)
		return myList
	myCopy = list(myList).copy()
	if element in myCopy:
		myCopy.remove(element)
	return myCopy


def ListFlatten(list_of_lists):
	return list(itertools.chain.from_iterable(list_of_lists))


def ListReplace(myList, replaceDict):
	newList = [replaceDict[x] if x in replaceDict else x for x in myList]
	return newList


def ListIntersect(orderList, otherList):
	return [x for x in orderList if x in otherList]


def ListInsert(myList, position, element):
	myCopy = list(myList).copy()
	myCopy.insert(position, element)
	return myCopy


def MergeDictList(myList):
	return {k: v for d in myList for k, v in d.items()}


def DictAdd(myDict, element, key):
	myDict = myDict.copy()
	myDict[element] = key
	return myDict


def DictRemove(myDict, element):
	myCopy = myDict.copy()
	if isinstance(element, dict):
		for name in element.keys():
			myDict = DictRemove(myDict, name)
		return myDict
	if isinstance(element, list):
		for name in element:
			myDict = DictRemove(myDict, name)
		return myDict
	if element in myCopy:
		myCopy.pop(element)
	return myCopy


def ListReverse(myList):
	myCopy = list(myList).copy()
	myCopy.reverse()
	return myCopy


def PartialInitDictDefaults(defaultValues, dictKeys):
	# Initialise a dict from a potentially larger set of defaults.
	return {k : defaultValues[k] for k in (defaultValues.keys() & dictKeys)}


def ListUnique(myList):
	return list(dict.fromkeys(myList))


def ListToListDict(myList):
	return {i : v for i, v in enumerate(myList)}


def ListDictToList(myDict):
	# A ListDict is a dict with keys [0, n - 1]
	listOut = list(range(len(myDict)))
	for i, v in myDict.items():
		if i not in listOut:
			trace.PrintSemanticTrace()
			raise ValueError("ListDict key invalid or out of bounds. Check list-map overrides?")
		listOut[i] = v
	return listOut


def PowerListAux(myList):
	# Generates the 'power set' of the list, preserving order and duplicates.
	if len(myList) == 0:
		return [[]]
	smallerList = myList.copy()
	smallerList.pop(0)
	recurResult = PowerListAux(smallerList)
	return recurResult + [[myList[0]] + k for k in recurResult]


def PowerList(myList):
	# Wrapper for PowerListAux.
	return PowerListAux(myList.copy())

def RaiseWrapper(text):
	raise ValueError(text)


def StartUpper(myStr):
	return myStr[0].upper() +  myStr[1:]

def FixKeys(myDict):
	return {int(i) if i.isnumeric() else RaiseWrapper("Non-numeric key in map restricted map. Check list-map overrides?") : v for i, v in myDict.items()}


def FillDefaults(params, default, doCopy=True, mergeList=False, debug=False, needMergeStyle=False):
	if type(params) != type({}):
		params = {}
	else:
		params = copy.deepcopy(params)
	for key, value in default.items():
		if key not in params:
			if doCopy and type(value) is dict or type(value) is list:
				params[key] = copy.deepcopy(value)
			else:
				params[key] = value
		elif type(value) is dict:
			params[key] = FillDefaults(params[key].copy(), value, needMergeStyle=needMergeStyle)
		elif type(value) is list:
			if type(params[key]) is dict:
				# Overrides are entered as a partial ListDict
				params[key] = ListDictToList(FillDefaults(FixKeys(params[key]), ListToListDict(value), needMergeStyle=needMergeStyle))
			elif type(params[key]) is list:
				if key + '_list_merge_style' not in params:
					if needMergeStyle:
						raise ValueError("Model spec error: Undefined list merge. See <key>_list_merge_style.")
					# Default to overwrite. Nothing needs to be done. See below.
				else:
					mergeStyle = params[key + '_list_merge_style']
					if mergeStyle == 'append' or mergeStyle == 'prepend':
						toAdd = params[key]
						params[key] = copy.deepcopy(value)
						if mergeStyle == 'append':
							params[key] = params[key] + toAdd
						else:
							params[key] = toAdd + params[key]
					elif mergeStyle == 'elementwise':
						params[key] = ListDictToList(FillDefaults(ListToListDict(params[key]), ListToListDict(value), needMergeStyle=needMergeStyle))
					# Note that merge style 'overwrite' requires no handling as
					# the default is overridden automatically since  the params
					# is being used as the base dicts (rather than the default). 
					params.pop(key + '_list_merge_style')
			elif mergeList:
				params[key] = ListDictToList(FillDefaults(ListToListDict(params[key]), ListToListDict(value), needMergeStyle=needMergeStyle))
	
	return params


def MergeCopy(param, default):
	# Wrapper for FillDefaults that handles non-dicts
	if param is None:
		if default is None:
			return None
		return default
	if type(param) is dict:
		if type(default) is dict:
			return FillDefaults(param, default)
		elif type(default) is list:
			return ListDictToList(FillDefaults(FixKeys(param), ListToListDict(default)))
	return param


def DictMerge(dict1, dict2):
	dict2 = dict2.copy()
	dict2.update(dict1)
	return dict2


def ReadDef(myDict, key, default):
	return myDict[key] if key in myDict else default


def RecursiveReplace(data, replaceValues):
	# Search json structure for 
	if type(data) is dict:
		for key, value in data.items():
			data[key] = RecursiveReplace(value, replaceValues)
	elif type(data) is list:
		for key, value in enumerate(data):
			data[key] = RecursiveReplace(value, replaceValues)
	elif data in replaceValues:
		return replaceValues[data]
	return data


def SetIndex(df, toSet):
	if df.index.names != [None]:
		df = df.reset_index()
	toSet = [x for x in toSet if x in df.columns]
	if len(toSet) == 0:
		return df
	df = df.set_index(toSet).sort_index()
	return df


def SetIndexCols(df, strataNames):
	baseStrata = ['year_of_birth', 'year_start', 'year', 'age', 'agecategory']
	return SetIndex(df, baseStrata + [x for x in strataNames if x not in baseStrata])


def IndexToFront(df, indexName, axis=0):
	otherIndexNames = [x for x in df.index.names if x != indexName]
	df = df.reorder_levels([indexName] + otherIndexNames, axis=axis)
	return df.sort_index(axis=axis)


def IncrementAge(df, maxAge, years_per_timestep=1):
	tableIndex = df.index.to_frame()
	tableIndex.age += years_per_timestep
	df.index = pd.MultiIndex.from_frame(tableIndex)
	# df.index = df.index.set_levels(df.index.get_level_values('age') + 1, level='age')
	
	# TODO very much tied to years_per_timestep=1
	df = df.drop(index=maxAge, level='age')
	return df


def FilterOnIndex_Alternate(df, indexName, minVal=False, maxVal=False):
	indexNames = list(df.index.names)
	df = IndexToFront(df, indexName)
	dfIndex = df.index.to_frame()
	if minVal is not False:
		minExisting = max(dfIndex[indexName].min(), minVal)
	if maxVal is not False:
		maxExisting = min(dfIndex[indexName].max(), maxVal - 1)
	df = df.loc[(slice(minExisting, maxExisting)), :]
	df = df.reorder_levels(indexNames)
	return df


def FilterOnIndex(df, indexName, minVal, maxVal, rawFilter=False):
	filterIndex = df.index.get_level_values(indexName)
	minExisting = max(filterIndex.min(), minVal)
	maxExisting = min(filterIndex.max(), maxVal - 1)
	filterIndex = ((filterIndex >= minExisting) & (filterIndex <= maxExisting))
	if rawFilter:
		return filterIndex
	df = df[filterIndex]
	#CondPrint('OLDOLDOLDOLDOLDOLDOLDOLD')
	#CondPrint(FilterOnIndex_Alternate(df, indexName, minVal, maxVal))
	#CondPrint('NEWNEWNEWNEWNEW', maxExisting)
	#CondPrint(df)
	return df


def GetMultiIndexFilter(df, targetIndex, filterIndex=False, allowMissing=False):
	for key, value in targetIndex.items():
		if key not in df.index.names:
			if not allowMissing:
				raise ValueError('GetMultiIndexFilter missing level {}'.format(key))
		else:
			keyValues = df.index.get_level_values(key)
			if type(value) is dict:
				if 'lower' in value:
					if 'upper' in value:
						minExisting = max(keyValues.min(), value['lower'])
						maxExisting = min(keyValues.max(), value['upper'] - 1)
						newFilter = ((keyValues >= minExisting) & (keyValues <= maxExisting))
					else:
						minExisting = max(keyValues.min(), value['lower'])
						newFilter = (keyValues >= minExisting)
				elif 'upper' in value:
					maxExisting = min(keyValues.max(), value['upper'] - 1)
					newFilter = (keyValues <= maxExisting)
				elif 'names' in value:
					newFilter = keyValues.isin(value['names'])
			elif type(value) is list:
				newFilter = keyValues.isin(value)
			else:
				newFilter = (keyValues == value)
			
			if filterIndex is False:
				filterIndex = newFilter
			else:
				filterIndex = (filterIndex & newFilter)
	if filterIndex is False:
		return pd.DataFrame(True, index=df.index, columns=df.columns)
	return filterIndex


def FilterOnMultiIndex(df, targetIndex, **kwargs):
	return df[GetMultiIndexFilter(df, targetIndex, **kwargs)]


def FilterOutIndexLevel(df, levelName, levelVal, **kwargs):
	df = df[GetMultiIndexFilter(df, {levelName : levelVal}, **kwargs)]
	df = df.droplevel(levelName)
	return df


def FilterOutMultiIndex(df, targetIndex, **kwargs):
	df = df[GetMultiIndexFilter(df, targetIndex, **kwargs)]
	for name in targetIndex.keys():
		if len(df.index.names) <= 1:
			# Return a single row as a series if all levels are dropped.
			df = df.reset_index(drop=True).loc[0]
		else:
			df = df.droplevel(name)
	return df


def FilterOnColValues(df, paramFilter):
	for col, data in paramFilter.items():
		if type(data) is dict:
			if 'lower' in data:
				df = df[df[col] >= data['lower']]
			if 'upper' in data:
				df = df[df[col] < data['upper']]
			if 'names' in data:
				df = df[df[col] == data['names']]
		else:
			df = df[df[col] == data]
	return df


def FilterOnIndexInherit(df, indexName, otherDf):
	otherValues = otherDf.index.get_level_values(indexName)
	lower = otherValues.min()
	upper = otherValues.max() + 1
	return FilterOnIndex(df, indexName, lower, upper)


def IndexValueDiff(df, processStrata, diffType='sub'):
	indexNames = ListRemove(list(df.index.names), list(processStrata.keys()))
	dfRel, dfBase = df.copy(), df.copy()
	for strata, variety in processStrata.items():
		dfRel = IndexToFront(dfRel, strata).transpose()
		dfRel = dfRel[variety[1]].transpose()
		dfBase = IndexToFront(dfBase, strata).transpose()
		dfBase = dfBase[variety[0]].transpose()
	
	if diffType == 'sub':
		dfRel = dfRel - dfBase
	elif diffType == 'div':
		dfRel = dfRel / dfBase
		dfRel = dfRel.replace([np.inf, -np.inf], np.nan)
		dfRel = dfRel.fillna(1)
		
	if len(indexNames) > 1:
		dfRel = dfRel.reorder_levels(indexNames)
	return dfRel


def SafeIndexToFrame(index):
	if isinstance(index, pd.MultiIndex):
		return index.to_frame(index=False)
	elif isinstance(index, pd.Index):
		return pd.DataFrame(index.values, columns=[index.name])
	else:
		raise ValueError("Input must be a MultiIndex or Index.")


def AgeToCohorts(df, period, offset):
	indexNames = [x for x in df.index.names if x != None]
	if len(indexNames) == 0:
		df = df.reset_index(drop=True)
	else:
		df = df.reset_index()
	df = df[df['age'] % period == offset]
	df = df.set_index(indexNames)
	return df


def AddAge(df, max_age):
	indexNames = [x for x in df.index.names if x != None]
	if 'age' in indexNames:
		return df
	if len(indexNames) == 0:
		df = df.reset_index(drop=True)
	else:
		df = df.reset_index()
	
	if 'age' not in df.columns:
		df = CrossDf(df, pd.DataFrame({'age' : list(range(max_age))}))
	df = df.set_index(['age'] + indexNames)
	return df


strataDfCache = {}
def GetStrataDf(name, values):
	global strataDfCache
	if name not in strataDfCache:
		strataDfCache[name] = pd.DataFrame({name: values})
	return strataDfCache[name]


def AddIndexLevel(df, indexName, indexVal, toTopLevel=False, dropNone=False):
	# Always returns a dataframe
	otherIndexNames = [x for x in df.index.names if x != None]
	if indexName in otherIndexNames:
		if dropNone and None in df.index.names:
			df = df.droplevel(None)
		if isinstance(df, pd.Series):
			return df.to_frame()
		return df
	
	if not isinstance(indexVal, list):
		if isinstance(df, pd.Series):
			index = df.index.to_frame()
			index[indexName] = indexVal
			index[df.name] = df
			index = index.set_index(indexName, append=True)
			index[indexName] = indexVal
			df = index[[df.name]]
			if toTopLevel:
				reorder = [len(df.index.names) - 1] + list(range(0, len(df.index.names) - 1))
				df = df.reorder_levels(reorder, 0)
			return df
		df = df.copy()
		df[indexName] = indexVal
		df = df.set_index(indexName, append=True)
		if dropNone and None in df.index.names:
			df = df.droplevel(None)
		if toTopLevel:
			reorder = [len(df.index.names) - 1] + list(range(0, len(df.index.names) - 1))
			df = df.reorder_levels(reorder, 0)
		return df
	
	df = pd.concat({name : df for name in indexVal}, names=[indexName])
	if not toTopLevel:
		reorder = list(range(1, len(df.index.names))) + [0]
		df = df.reorder_levels(reorder, 0)
	if dropNone and None in df.index.names:
		df = df.droplevel(None)
	return df


def AddColLevel(df, indexName, indexVal):
	return AddIndexLevel(df.transpose(), indexName, indexVal).transpose()


def DropNoneIndexLevel(df):
	if None not in df.index.names:
		return df
	otherIndexNames = [x for x in df.index.names if x != None]
	index = df.index.to_frame()
	index = index[otherIndexNames]
	df.index = pd.MultiIndex.from_frame(index)
	return df


def ExpandToCategoricalStrata(df, strataCats,
		excludeStrata=False,
		skipDataValidation=False,
		reverseOrder=False,
		dropNoneLevel=True):
	existingStrata = list(df.reset_index().columns)
	for strata, varieties in strataCats.items():
		if (excludeStrata is not False) and strata in excludeStrata:
			if strata in df.reset_index():
				trace.PrintSemanticTrace()
				raise ValueError('Table supplied with unexpected strata {}'.format(strata))
		elif strata in existingStrata:
			if (not skipDataValidation) and set(varieties) != set(df.index.to_frame()[strata].values):
				trace.PrintSemanticTrace()
				CondPrint("Strata {} exists but is incomplete.".format(strata))
				CondPrint("Expecting {}".format(varieties))
				CondPrint("Found {}".format(list(set(df.index.to_frame()[strata].values))))
				CondPrint(df)
				raise ValueError('Strata Error')
		else:
			df = AddIndexLevel(df, strata, varieties, toTopLevel=reverseOrder)
	if dropNoneLevel:
		df = DropNoneIndexLevel(df)
	return df


def FillMissingIndexCombinations(df, fillValue=0):
	index = df.index.to_frame()
	strata = {}
	for col in index.columns:
		strata[col] = list(set(index[col]))
	
	dfFull = ExpandToCategoricalStrata(
		pd.DataFrame({col : fillValue for col in df.columns}, index=[0]),
		strata)
	dfFull.update(df)
	return dfFull


def ExpandIntegerStrata(df, strata, minValue, maxValue):
	indexNames = [x for x in df.index.names if x != None]
	noIndex = (len(indexNames) == 0)
	
	# Index lacks strata, expand it.
	if strata not in indexNames:
		df = AddIndexLevel(df, strata, list(range(minValue, maxValue)))
		return df
	
	if minValue not in df.index.get_level_values(strata):
		CondPrint(df)
		raise ValueError("PMSLT data error: {} index missing data for min value {}.".format(strata, minValue))
	
	indexNames = [x for x in indexNames if (x != strata and x != None)]
	if noIndex:
		df = df.reset_index(drop=True)
	else:
		df = df.reset_index()
	
	# Add full values for the strata
	df = CrossDf(df, pd.DataFrame({'_expanded_strata' : list(range(minValue, maxValue))}))
	df = df[df['_expanded_strata'] >= df[strata]]
	
	# Add a copy of strata so it can be grabbed with loc
	df['_strata_as_index'] = df[strata]
	df['_expanded_strata_2'] = df[strata]
	df[strata] = df['_expanded_strata']
	df = df.set_index([strata, '_strata_as_index'])
	df = df.loc[df.groupby([strata])['_expanded_strata_2'].idxmax()]
	df = df.drop(columns=['_expanded_strata', '_expanded_strata_2']).droplevel('_strata_as_index')
	df = df.reset_index().set_index([strata] + indexNames)
	return df


def ExpandAgeCategory(
		df, max_age, addZero=False, addZeroVals=False, ignoreMissingZero=False,
		ignoreLengthCheck=False, splitAggregate=False, targetColumn='agecategory'):
	indexNames = [x for x in df.index.names if x != None]
	noIndex = (len(indexNames) == 0)
	# Index already has age.
	if 'age' in indexNames:
		return df
	
	
	if targetColumn in indexNames:
		if (not ignoreMissingZero) and (0 not in df.index.get_level_values(targetColumn)):
			if addZero:
				otherIndex = df.reset_index().set_index(ListRemove(indexNames, targetColumn)).index.to_frame().drop_duplicates()
				columns = [targetColumn] + list(df.columns)
				otherIndex[columns] = 0
				if addZeroVals is not False:
					for col in columns:
						if col in addZeroVals:
							otherIndex[col] = addZeroVals[col]
				otherIndex = otherIndex[columns]
				otherIndex = otherIndex.reset_index().set_index(indexNames)
				df = pd.concat([df, otherIndex])
			else:
				#pdb.set_trace()
				CondPrint(df)
				raise ValueError("PMSLT data error: agecategory index missing age 0.")
	else:
		df[targetColumn] = 0
	
	indexNames = [x for x in indexNames if (x != targetColumn and x != None)]
	if noIndex:
		df = df.reset_index(drop=True)
	else:
		df = df.reset_index()
		
	# Add age and filter out ages that are below the agecategory.
	df = CrossDf(df, pd.DataFrame({'age' : list(range(max_age))}))
	df = df[df['age'] >= df[targetColumn]]
	
	# Add a copy of agecategory to the index so it can be grabbed with loc
	df['as_index'] = df[targetColumn]
	df = df.set_index(['age', 'as_index'])
	df = df.loc[df.groupby(['age'])[targetColumn].idxmax()]
	
	if splitAggregate:
		# The values are aggregates not rates, so values have to be rescaled
		# so that the sum of the columns is not changed.
		counts = dict(df[targetColumn].value_counts())
		dfCounts = pd.DataFrame({targetColumn : counts.keys(), 'agesCovered' : counts.values()}).set_index(targetColumn)
		df = df.join(dfCounts, targetColumn)
		
		indexCombinations = 1
		for name in indexNames:
			count = len(list(set(list(df[name]))))
			indexCombinations = indexCombinations * count
		df['agesCovered'] = df['agesCovered'] / indexCombinations
		allInteger = np.array_equal(df['agesCovered'], df['agesCovered'].astype(int))
		if not allInteger:
			raise ValueError('Non-integer agesCovered in ExpandAgeCategory.')
	
	df = df.drop(columns=[targetColumn]).droplevel('as_index')
	df = df.reset_index().set_index(['age'] + indexNames)
	
	if splitAggregate:
		df = df.div(df['agesCovered'], axis=0)
		df = df.drop(columns=['agesCovered'])

	if len(df) % max_age != 0 and not ignoreLengthCheck:
		fullDf = FillMissingIndexCombinations(df).sort_index()
		diff = set(list(fullDf.index)).difference(set(list(df.index)))
		print(diff)
		print(len(list(diff)))
		print('max_age', max_age)
		print(df)
		print(fullDf)
		raise ValueError('Unable to expand agecategory. Check that the dimensions are sorted and filled evenly.')
	return df


def FillYoungAges(df, value=0, index='age'):
	minAge = min(list(df.index.get_level_values(index)))
	if minAge == 0:
		return df.copy()
	indexOrder = list(df.index.names)
	
	dfYoung = FilterOutIndexLevel(df, index, minAge) * 0 + value
	if minAge == 1:
		dfYoung = AddIndexLevel(dfYoung, 'age', 0)
	else:
		dfYoung = AddIndexLevel(dfYoung, 'age', list(range(minAge)))
	dfYoung = dfYoung.reorder_levels(indexOrder)
	df = pd.concat([df, dfYoung])
	df = df.sort_index()
	return df


def SnapSeriesToValues(series, values, mode='down'):
	"""
	Snap each value in the input series to the nearest value in the input values list, according to the specified mode.
	(80% written by ChatGPT)

	Parameters:
	- series: pandas series containing numeric values
	- values: list of numeric values to snap each element in the series to
	- mode: string specifying the snapping mode. Must be one of 'up', 'down', or 'closest'. Default is 'closest'.

	Returns:
	- pandas series of the same length as the input series, where each value is the nearest value in the input values list according to the specified mode
	"""

	# convert the input series and values list to numpy arrays
	series_array = np.array(series)
	values_array = np.array(values)

	# subtract each value in the input series from each value in the input values list
	differences = series_array.reshape(-1, 1) - values_array.reshape(1, -1)

	# determine the index of the closest value in the values list for each series value
	if mode == 'up':
		closest_index = np.argmax(np.where(differences <= 0, differences, -np.inf), axis=1)
	elif mode == 'down':
		closest_index = np.argmin(np.where(differences >= 0, differences, np.inf), axis=1)
	elif mode == 'closest':
		closest_index = np.argmin(np.abs(differences), axis=1)
	else:
		raise ValueError('Invalid mode {} for SnapSeriesToValues'.format(mode))

	# use the index to lookup the closest value in the values list for each series value
	snapped_values = values_array[closest_index]

	# return the result as a pandas series
	return pd.Series(snapped_values, index=series.index)


def RebucketIndexValues(df, indexName, anchors, doMean=False):
	indexOrder = list(df.index.names)
	index = df.index.to_frame()
	index['_aggindex'] = SnapSeriesToValues(index[indexName], anchors, mode='down')
	df.index = pd.MultiIndex.from_frame(index)
	if doMean:
		df = df.groupby(ListRemove(df.index.names, indexName)).mean()
	else:
		df = df.groupby(ListRemove(df.index.names, indexName)).sum()
	df.index = df.index.set_names(indexName, level='_aggindex')
	df.index = df.index.reorder_levels(indexOrder)
	df = df.sort_index()
	return df


def AggregateColumns(df, aggMap):
	dfAgg = pd.DataFrame()
	for key, value in aggMap.items():
		dfAgg[key] = df[value].sum(axis=1)
	return dfAgg


def ExpandToValueAtAge(df, special_age, max_age):
	indexNames = [x for x in df.index.names if x != None]
	if len(indexNames) == 0:
		df = df.reset_index(drop=True)
	else:
		df = df.reset_index()
	newStrata = [0, special_age, special_age + 1]
	if special_age == 0:
		newStrata = [0, 1]
	df = CrossDf(df, pd.DataFrame({'agecategory' : newStrata}))
	df = df.set_index(['agecategory'] + indexNames)
	for val in newStrata:
		if val != special_age:
			df.loc[val, :] = 0

	df = ExpandAgeCategory(df, max_age)
	return df


def IndexAgeToYob(df, year, inplace=False):
	index = df.index.to_frame()
	index['yob'] = year - index['age']
	index = index.drop('age', axis=1)
	if not inplace:
		df = df.copy()
	df.index = pd.MultiIndex.from_frame(index)
	return df


def IndexYobToAge(df, year, inplace=False):
	index = df.index.to_frame()
	index['age'] = year - index['yob']
	index = index.drop('yob', axis=1)
	if not inplace:
		df = df.copy()
	df.index = pd.MultiIndex.from_frame(index)
	return df


def ApplyApc(col, year, apcLimit, apcCol, yearCol=False, yearMinApc=False):
	if yearMinApc is False:
		yearMinApc = year
	if yearCol is not False:
		return col * (
			((1.0 + apcCol).clip(lower=0)) **
			np.clip(year - yearMinApc, 0, yearCol))
	else:
		return col * (
			((1.0 + apcCol).clip(lower=0)) **
			min(apcLimit, year - yearMinApc))


def ExpandApcToYears(df, apcLimit):
	apcCols = [x[:-4] for x in df.columns if x[-4:] == '_apc']
	apcYearCols = [x[:-10] for x in df.columns if x[-10:] == '_apc_years']
	if len(apcCols) == 0:
		return df
	
	maxApcYears = apcLimit
	for col in apcYearCols:
		maxApcYears = max(maxApcYears, df[col].max())
	
	dfOut = pd.DataFrame()
	for year in range(maxApcYears):
		dfYear = df.copy()
		for col in apcCols:
			dfYear[col] = ApplyApc(
				df[col], year, apcLimit,
				df[col + '_apc'], 
				yearCol=df[col + '_apc_years'] if col in apcYearCols else False, 
				yearMin=0)
		dfYear = AddIndexLevel(dfYear, 'year_start', year)
		dfOut = pd.concat([dfOut, dfYear])
	return dfOut


def PossiblyClip(df, lower=False, upper=False):
	if upper is not False:
		if lower is not False:
			df = df.clip(lower=lower, upper=upper)
		else:
			df = df.clip(upper=upper)
	elif lower is not False:
		df = df.clip(lower=lower)
	return df


def ValueToValueRange(df, name, offset):
	indexNames = [x for x in df.index.names if (x != None and x != name)]
	if len(indexNames) == 0:
		df = df.reset_index(drop=True)
	else:
		df = df.reset_index()
	df['{}_end'.format(name)] = df[name] + offset
	df = df.rename(columns={name : '{}_start'.format(name)})
	df = df.set_index(['{}_start'.format(name), '{}_end'.format(name)] + indexNames)
	return df


def ToHeatmap(df, structure, rowEndCols=False):
	df = df.reset_index()
	
	df['_sort_row'] = ''
	for name, value in structure['sort_rows'].items():
		if name in df.columns:
			repDict = {x : str(i).zfill(2) for i, x in enumerate(value)}
			df['_sort_row'] = df['_sort_row'] + df[name].replace(repDict).astype(str)
	df['_sort_col'] = ''
	for name, value in structure['sort_cols'].items():
		if name in df.columns:
			repDict = {x : str(i).zfill(2) for i, x in enumerate(value)}
			df['_sort_col'] = df['_sort_col'] + df[name].replace(repDict).astype(str)
	
	df = df.set_index(
		['_sort_row', '_sort_col'] + 
		list(structure['sort_rows'].keys()) + 
		list(structure['sort_cols'].keys()))
	df = df.unstack(['_sort_col'] + list(structure['sort_cols'].keys()))
	df = df.sort_index(axis=0, level=0)
	df = df.sort_index(axis=1, level=0)
	
	df.columns = df.columns.droplevel(level='_sort_col')
	if len(df.index.names) > 1:
		if len(df.columns.names) > 1:
			df.columns = df.columns.droplevel(level=0)
		df.index = df.index.droplevel(level='_sort_row')
	else:
		df = df.reset_index(drop=True)
		df = df.rename(index={0 : 'value'})
		
	if rowEndCols is not False:
		for endName, dfEnd in rowEndCols.items():
			dfEnd = dfEnd.reset_index()
			dfEnd['_sort_row'] = ''
			for name, value in structure['sort_rows'].items():
				if name in dfEnd.columns:
					repDict = {x : str(i).zfill(2) for i, x in enumerate(value)}
					dfEnd['_sort_row'] = dfEnd['_sort_row'] + dfEnd[name].replace(repDict).astype(str)
			dfEnd = dfEnd.set_index(['_sort_row'] + list(structure['sort_rows'].keys()))
			dfEnd = dfEnd.sort_index(axis=0, level=0)
			dfEnd.index = dfEnd.index.droplevel(level='_sort_row')
			df[tuple([endName]*len(structure['sort_rows'].keys()))] = dfEnd
	return df


def RandomListOfOnesAndZeros(length, num_ones, copies=1, prng=None):
	if num_ones > length:
		raise ValueError("Number of ones cannot exceed the length of the list.")

	if prng is None:
		prng = np.random.RandomState()

	# Create an array with the desired number of ones and zeros
	ones = np.ones(num_ones, dtype=int)
	zeros = np.zeros(length - num_ones, dtype=int)

	# Create a list to store the shuffled copies
	shuffled_copies = []
	# Define a function to generate a random shuffled list
	def generate_shuffled_list(x):
		shuffled_list = np.concatenate((ones, zeros))
		prng.shuffle(shuffled_list)
		return shuffled_list

	# Generate a 2D array of shuffled copies using apply_along_axis
	random_lists = np.apply_along_axis(generate_shuffled_list, axis=1, arr=np.empty((copies, length)))

	return random_lists.flatten()



def GetLogNormal(mean, std):
	# Parameterisation from https://stackoverflow.com/a/73567355
	mean = mean.astype(np.float64)
	std = std.astype(np.float64)
	a = 1 + (std / mean) ** 2
	s = np.sqrt(np.log(a))
	scale = mean / np.sqrt(a)
	distr = scipy.stats.lognorm(s, 0, scale)
	
	#CondPrint('mean', mean, 'std', std)
	#CondPrint('mean calc', distr.mean())
	#CondPrint('std calc', distr.std())
	#CondPrint('quartiles', distr.ppf(0.25), distr.ppf(0.5), distr.ppf(0.75))
	#fig, ax = plt.subplots(1, 1)
	#x = np.linspace(0, 10, 100)
	#ax.plot(x, scipy.stats.lognorm.pdf(x, s=std, scale=mean), 'r-', lw=5, alpha=0.6, label='lognorm pdf')
	#bla = 1/0
	return distr


def GetLogNormalMedianLogScale(median, logStd):
	# Parameterisation from https://stackoverflow.com/a/73567355
	distr = scipy.stats.lognorm(scale=median, s=logStd)
	
	#CondPrint('np.log(median)', median, 'std', logStd)
	#CondPrint('mean calc', distr.mean())
	#CondPrint('std calc', distr.std())
	#CondPrint('quartiles', distr.ppf(0.25), distr.ppf(0.5), distr.ppf(0.75))
	#fig, ax = plt.subplots(1, 1)
	#x = np.linspace(0, 10, 100)
	#ax.plot(x, scipy.stats.lognorm.pdf(x, median, 0, logStd), 'r-', lw=5, alpha=0.6, label='lognorm pdf')
	return distr


normalRangeCache = {}
def GetNormalRange(mean, std, lower, upper, log=False):
	lazyHash = '{},{},{},{}'.format(mean, std, lower, upper)
	if lazyHash not in normalRangeCache:
		# Calculating a lot of normal ranges is expensive
		if log:
			distr = GetLogNormalMedianLogScale(mean, std)
			# TODO Get log normal is correct but often not useful, since I get given sd on the log scale. Fix it?
		else:
			distr = scipy.stats.norm(mean, std)
		#res, error = scipy.integrate.quad(
		#	lambda x: distr.pdf(x), lower, upper)
		area = distr.cdf(upper) - distr.cdf(lower)
		#CondPrint('res', res, 'area', area)
		normalRangeCache[lazyHash] = area
	return normalRangeCache[lazyHash]


normalMeanCache = {}
def GetNormalMean(mean, std, lower, upper, log=False, useGaussQuad=False):
	lazyHash = '{},{},{},{}'.format(mean, std, lower, upper)
	if lazyHash not in normalMeanCache:
		if log:
			distr = GetLogNormalMedianLogScale(mean, std)
		else:
			distr = scipy.stats.norm(mean, std)
		
		oldErrState = np.geterr()
		np.seterr(all='ignore') # Integrate underflow that persists with very small ranges.
		if useGaussQuad is False:
			# Do full precision
			res, error = scipy.integrate.quad(
				lambda x: x*distr.pdf(x), lower, upper)
		else:
			# Uses a Gaussian quadrature.
			#CondPrint('lower, upper', lower, upper)
			#CondPrint('distr.pdf(x)', distr.pdf(lower), distr.pdf(upper))
			res, error = scipy.integrate.quad(
				lambda x: x*distr.pdf(x), lower, upper)
		normalMeanCache[lazyHash] = res
		np.seterr(**oldErrState)
	return normalMeanCache[lazyHash]


def GetSpaceSize(dimensions):
	mult = 1
	for dim in dimensions:
		mult = mult * len(dim)
	return mult


def PickNthElementFromSpace(dimensions, n):
	# Selects the nth (zero indexed) element of a list of lists, where
	# the lists define a lexicographic ordering of all the points in
	# the multidimensional space defined by taking each of the inner
	# lists as a dimension.
	point = []
	for dim in ListReverse(dimensions):
		options = len(dim)
		pick = n % (options)
		n = int((n - pick) / options)
		point.append(dim[pick])
	return ListReverse(point)
	
 
def RecursiveApplyAppend(data):
	if type(data) is list:
		for element in data:
			if type(element) is list or type(element) is dict:
				RecursiveApplyAppend(element)
		return data
	
	for key, value in data.items():
		if type(value) is list or type(value) is dict:
			data[key] = RecursiveApplyAppend(value)
		elif key + '_append_' in data:
			data[key] = value + data[key + '_append_']
	
	for key in list(data.keys()):
		if '_append_' in key:
			del data[key]
	return data


def AddPartialOverlap(dfA, dfB, default):
	sharedCols = list(set().union(dfA.columns, dfB.columns))
	return dfA.reindex(columns=sharedCols, fill_value=default) + dfB.reindex(columns=sharedCols, fill_value=default)


def FullCrossProduct_unpacked(table):
	result = [{'_' : 1}]
	for dimension, values in table.items():
		newResult = []
		for v in values:
			newResult = newResult + [DictAdd(x, dimension, v) for x in result]
		result = newResult
	result = [DictRemove(x, '_') for x in result]
	return result

def FullCrossProduct(dimensions):
	# Optimised, or at least pythonised, version of the above.
	keys = dimensions.keys()
	values = dimensions.values()
	result = [dict(zip(keys, combination)) for combination in itertools.product(*values)]
	return result


def ZipCrossProduct(baseTables, zipTable):
	returnData = []
	for baseData in baseTables:
		newData = []
		zipLength = False
		
		for zipKey, zipData in zipTable.items():
			if zipLength is False:
				zipLength = len(zipData)
				for i in range(zipLength):
					newData.append(baseData.copy())
					
			if len(zipData) != zipLength:
				raise ValueError('zipTable length mismatch ({} and {}) for key {}.'.format(
					len(zipData), zipLength, zipKey))
			
			for i, zipValue in enumerate(zipData):
				default = newData[i][zipKey] if zipKey in newData[i] else None
				newData[i][zipKey] = MergeCopy(zipValue, default)
		returnData = returnData + newData
	return returnData


def UnpackTableMultipliers(data, CsvLoader):
	# If the input dict data contains 'zipTable', then it is "zipped" up into a
	# list of dicts, copying the other contents of data to each dict.
	# 'zipTable' must be a dict with data that consists of lists of equal size.
	
	if 'zipTable' in data:
		zipTableList = data['zipTable']
		newData = [DictRemove(data, 'zipTable')]
		
		# Generate the list of zip tables to apply sequentially.
		if type(zipTableList) is not list:
			zipTableList = [zipTableList]
		
		for zipTable in zipTableList:
			# Load zip table from a file
			if type(zipTable) is str:
				df = CsvLoader(zipTable)
				if df is False:
					raise ValueError('Cannot find zip table csv {}'.format(zipTable))
				zipTable = {col : list(df[col]) for col in df.columns}
			newData = ZipCrossProduct(newData, zipTable)
	else:
		newData = [data]
	return newData


def GetYearRangeFromConf(conf, year_start, year_end):
	if 'year' in conf and conf['year'] is not False:
		year_start = conf['year']
	elif 'year_start' in conf and conf['year_start'] is not False:
		year_start = conf['year_start']
		
	if 'year' in conf and conf['year'] is not False:
		year_end = conf['year'] + 1
	elif 'year_end' in conf and conf['year_end'] is not False:
		year_end = conf['year_end']
	elif 'duration' in conf and conf['duration'] is not False:
		year_end = year_start + conf['duration']
	return year_start, year_end


def ZerosDf(baseDf, columns):
	df = pd.DataFrame({ col : baseDf*0 for col in columns})
	return df


def OptExists(conf, keyList):
	if type(keyList) is list and len(keyList) <= 1:
		keyList = keyList[0]
	if type(keyList) is not list:
		return keyList in conf
	
	if keyList[0] not in conf:
		return False
	return OptExists(conf[keyList[0]], keyList[1:])


def Opt(conf, keyList, default=False):
	# Load an optional parameter (or path of parameters) from a dict, with a default if it is not found.
	if type(keyList) is list and len(keyList) <= 1:
		keyList = keyList[0]
	
	if type(keyList) is not list:
		if keyList in conf:
			return conf[keyList]
		else:
			return default
	
	if keyList[0] not in conf:
		return default
	return Opt(conf[keyList[0]], keyList[1:], default)


def OptBool(conf, key, default=False):
	# Conf is either a bool or a dict with bool values.
	if isinstance(conf, bool):
		return conf
	return Opt(conf, key, default=default)


def DictAdd(conf, keyList, newValue):
	# Add a parameter to a map at a path defined by key list.
	for name in keyList[:-1]:
		if name not in conf:
			conf[name] = {}
		conf = conf[name]
	conf[keyList[-1]] = newValue


def SanitiseName(name):
	return name.replace("/", "_")


def Sign(n):
	if n == 0:
		return 0
	elif n > 0:
		return 1
	return -1


def CrossListWithDictList(dictList, listName, listData, noCopy=False):
	returnDictList = []
	for newItem in listData:
		for crossTarget in dictList:
			if noCopy:
				target = crossTarget
			else:
				target = crossTarget.copy()
			target[listName] = newItem
			returnDictList.append(target)
	return returnDictList


def CrossListDictToDictList(listDict):
	returnDictList = [{}]
	for name, data in listDict.items():
		returnDictList = CrossListWithDictList(returnDictList, name, data)
	return returnDictList


def SplitCmdLineArgs(args):
	CondPrint(args)
	posArgs = []
	keyArgs = {}
	for arg in args:
		if len(arg) == 0 or arg[0] != '-':
			posArgs.append(arg)
		elif '=' in arg:
			argSplit = arg.split('=')
			if len(argSplit) > 2:
				raise ValueError('Two or more "=" found in argument "{}"'.format(arg))
			keyArgs[argSplit[0]] = argSplit[1]
		else:
			keyArgs[arg] = True

	return posArgs, keyArgs

def RunWithProfile(func, outputFile='profile', keepLineStr='pmslt'):
	pr = cProfile.Profile()
	pr.enable()
	
	func()
	
	pr.disable()
	s = io.StringIO()
	ps = pstats.Stats(pr, stream=s).sort_stats('cumtime')
	ps.print_stats()

	headerLines = 6
	with open(outputFile + '.txt', 'w+') as f:
		for line in s.getvalue().splitlines():
			headerLines -= 1
			if headerLines > 0 or keepLineStr in line.lower():
				f.write(line + '\n')


def PossiblyRunWithProfile(wantProfile, func):
	if wantProfile is False:
		func()
		return
	
	outputFile = 'profile' if wantProfile is True else wantProfile
	CondPrint('Profile output:', outputFile)
	RunWithProfile(func, outputFile=outputFile)
