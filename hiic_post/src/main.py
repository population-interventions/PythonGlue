import pandas as pd
import numpy as np
import json
from tqdm import tqdm

class AutoVivification(dict):
    """
	Implementation of perl's autovivification feature.
	"""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value

def read_data(base_path, run_id, params):
	"""
	Loads PMSLT output data based on keys specified in 'params'.

	Parameters:
	* base_path (str): Path to 'runs' folder
	* run_id (int): Run ID. Must correspond to a folder inside base_path
	* params (dict): A dictionary containing "age_start" and "age_end" keys

	Returns:
	* Pandas DataFrame or TextParser. 
	"""
	base_folder = f"{base_path}/{str(run_id)}"
	if params["type"] == "BAU":
		return pd.read_csv(f"{base_folder}/raw/output_lifetable_bau.csv")
	file_name = "_".join([
		"output_lifetable", 
		params["metric"], 
		str(params["age_start"]), 
		str(params["age_end"]),
		])
	return pd.read_csv(f"{base_folder}/raw/{file_name}.csv")


def get_outcome_difference_by_age(bau_df, int_df, params):
	"""
	Returns cumulative sum time-series of outcome difference for a specified 
	outcome (i.e. HALY, total_spent, total_income), by age range in future, 
	and sex. Used for 'period' interventions.

	Parameters:
	* bau_df (pandas.DataFrame): Dataframe corresponding to BAU results
	* int_df (pandas.DataFrame): Dataframe corresponding to intervention results
	* params (dict): A dictionary containing "age_start", "age_end", and "outcome" keys

	Returns:
	* output_difference (list): A cumulative sum time series of the specified outcome,
	for the specified age-sex group
	"""
	bau_outcome = bau_df.loc[
		(bau_df["age"].between(params["age_start"], params["age_end"])) &
		(bau_df["sex"] == params["sex"])
	].groupby("year").sum()[params["outcome"]]
	int_outcome = int_df.loc[
		(int_df["age"].between(params["age_start"], params["age_end"])) &
		(int_df["sex"] == params["sex"])
	].groupby("year").sum()[params["outcome"]]
	outcome_difference = np.cumsum(int_outcome.subtract(bau_outcome)).values.round(2).tolist()
	return outcome_difference


def get_outcome_difference_by_yob(bau_df, int_df, params):
	"""
	Returns cumulative sum time-series of outcome difference for a specified 
	outcome (i.e. HALY, total_spent, total_income), by year of birth, and sex.
	Used for 'cohort' interventions.

	Parameters:
	* bau_df (pandas.DataFrame): Dataframe corresponding to BAU results
	* int_df (pandas.DataFrame): Dataframe corresponding to intervention results
	* params (dict): A dictionary containing "age_start", "age_end", and "outcome" keys

	Returns:
	* output_difference (list): A cumulative sum time series of the specified outcome,
	for the cohort specified by input year-of-birth and sex.
	"""
	bau_outcome = bau_df.loc[
		(bau_df["year_of_birth"].between(2020 - params["age_end"], 2020 - params["age_start"])) &
		(bau_df["sex"] == params["sex"])
	].groupby("year").sum()[params["outcome"]]
	int_outcome = int_df.loc[
		(int_df["year_of_birth"].between(2020 - params["age_end"], 2020 - params["age_start"])) &
		(int_df["sex"] == params["sex"])
	].groupby("year").sum()[params["outcome"]]
	outcome_difference = np.cumsum(int_outcome.subtract(bau_outcome)).values.round(2).tolist()
	return outcome_difference

		
def period_int_output(bau_df, run_id, base_path, metric, age_categories, sex_categories, outcome_categories):
	"""
	Creates result key for 'period' interventions, i.e. interventions where age
	specifies age in the future.

	Parameters:
	* bau_df (pandas.DataFrame): Dataframe corresponding to BAU results
	* int_df (pandas.DataFrame): Dataframe corresponding to intervention results
	* run_id (int): Run ID. Must correspond to a folder inside base_path
	* base_path (str): Path to 'runs' folder
	* metric (str): Metric targeted by intervention, i.e. one of 'incidence',
	'disability', 'mortality'
	* age_categories (list): list of dictionaries specified start- and eng-age of 
	interventions. Of form: [{start_age: ..., end_age: ...}, {...}]
	* sex_categories (list): list of sexes.
	* outcome_categories (list): list of simulation outcomes, i.e. 'HALY', 'total_spent', 
	or 'total_income'

	Returns:
	* results (dict): A dictionary of results, indexed by age, outcome variable, and sex.
	For each age-outcome-sex combination, results are stored as a cumulative time-series
	of the outcome variable, beginning in 2020.
	"""
	OUTCOME_KEY_MAP = {
		"HALY": "halys", 
		"total_spent": "health_system_savings", 
		"total_income": "income_gain"
	}
	results = AutoVivification()
	params={}
	for age_category in age_categories:
		age_key = f"{age_category['age_start']}-{age_category['age_end']}"
		params["type"] = "INT" 
		params["metric"] = metric
		params["age_start"] = 0
		params["age_end"] = 110
		int_df = read_data(
			base_path=base_path,
			run_id=run_id,
			params=params,
		)	
		for outcome in outcome_categories:
			outcome_key = OUTCOME_KEY_MAP[outcome]
			params["outcome"] = outcome
			for sex_category in sex_categories:
				params["sex"] = sex_category
				outcome_difference = get_outcome_difference_by_age(
					bau_df=bau_df,
					int_df=int_df,
					params=params,
				)
				results[age_key][outcome_key][sex_category] = outcome_difference

	return results


def cohort_int_output(bau_df, run_id, base_path, metric, age_categories, sex_categories, outcome_categories):
	"""
	Creates result key for 'cohort' interventions, i.e. interventions where age
	specifies age in the base year (2020).

	Parameters:
	* bau_df (pandas.DataFrame): Dataframe corresponding to BAU results
	* int_df (pandas.DataFrame): Dataframe corresponding to intervention results
	* run_id (int): Run ID. Must correspond to a folder inside base_path
	* base_path (str): Path to 'runs' folder
	* metric (str): Metric targeted by intervention, i.e. one of 'incidence',
	'disability', 'mortality'
	* age_categories (list): list of dictionaries specified start- and eng-age of 
	interventions. Of form: [{start_age: ..., end_age: ...}, {...}]
	* sex_categories (list): list of sexes.
	* outcome_categories (list): list of simulation outcomes, i.e. 'HALY', 'total_spent', 
	or 'total_income'

	Returns:
	* results (dict): A dictionary of results, indexed by age, outcome variable, and sex.
	For each age-outcome-sex combination, results are stored as a cumulative time-series
	of the outcome variable, beginning in 2020.
	"""
	OUTCOME_KEY_MAP = {
		"HALY": "halys", 
		"total_spent": 
		"health_system_savings", 
		"total_income": 
		"income_gain"
	}
	results = AutoVivification()
	params={}
	params["type"] = "INT" 
	params["metric"] = metric
	params["age_start"] = 0
	params["age_end"] = 110
	int_df = read_data(
		base_path=base_path,
		run_id=run_id,
		params=params,
	)	
	for age_category in age_categories:
		age_key = f"{age_category['age_start']}-{age_category['age_end']}"
		params["age_start"] = age_category["age_start"]
		params["age_end"] = age_category["age_end"]
		for outcome in outcome_categories:
			outcome_key = OUTCOME_KEY_MAP[outcome]
			params["outcome"] = outcome
			for sex_category in sex_categories:
				params["sex"] = sex_category
				outcome_difference = get_outcome_difference_by_yob(
					bau_df=bau_df,
					int_df=int_df,
					params=params,
				)
				results[age_key][outcome_key][sex_category] = outcome_difference

	return results


def write_output(base_path, run_id, metric, int_type, results):
	"""
	Writes .json files in format suitable for website.


	Parameters:
	* base_path (str): Path to 'runs' folder
	* run_id (int): Run ID. Must correspond to a folder inside base_path
	* metric (str): Metric targeted by intervention, i.e. one of 'incidence',
	'disability', 'mortality'
	* int_type (str): One of 'cohort' or 'period'
	* results (dict): results object output by period_int_ouput and cohort_int_output
	functions

	Returns:
	None
	"""
	REDUCTION_KEY_MAP = {
		"rate_0.025": "00250",
		"rate_0.05": "00500",
		"rate_0.1": "01000",
		"rate_0.2": "02000",
		"rate_0.5": "05000",
	}
	output = {}
	metadata = open(f"{base_path}/{str(run_id)}/raw/params.txt", "r").read().splitlines()
	output["targetDisease"] = metadata[0]
	output["targetMetric"] = metric
	output["targetReduction"] = REDUCTION_KEY_MAP[metadata[1]]
	output["applicationType"] = int_type
	output["duration"] = metadata[3].replace("dur_", "")
	output["timeLag"] = metadata[2].replace("delay_", "")
	output["results"] = results

	file_name = "__".join([
		output["targetDisease"], 
		output["targetMetric"], 
		output["targetReduction"], 
		output["applicationType"], 
		output["duration"],
		output["timeLag"]
		])
	with open(f"output/{file_name}.json", "w") as f:
		json.dump(output, f, indent=4)	


def process_run(run_id, base_path, metrics, age_categories, sex_categories, outcome_categories):
	"""
	Produces output files for a corresponding 'run_id' folder.

	Parameters:
	* run_id (int): Run ID. Must correspond to a folder inside base_path
	* base_path (str): Path to 'runs' folder
	* metrics (list): list of metrics targeted by intervention, i.e. 'incidence',
	'disability', and 'mortality'
	* age_categories (list): list of dictionaries specified start- and eng-age of 
	interventions. Of form: [{start_age: ..., end_age: ...}, {...}]
	* sex_categories (list): list of sexes.
	* outcome_categories (list): list of simulation outcomes, i.e. 'HALY', 'total_spent', 
	or 'total_income'

	Returns:
	None
	"""
	metadata = open(f"{base_path}/{str(run_id)}/raw/params.txt", "r").read()
	print("-------------------------------------")
	print(f"run_id: {run_id}")
	print("-------------------------------------")
	print(metadata)
	
	params = {"type": "BAU"}
	bau_df = read_data(
		base_path=base_path,
		run_id=run_id,
		params=params,
	)
	for metric in metrics:
		period_results = period_int_output(
			bau_df=bau_df,
			run_id=run_id,
			base_path=base_path,
			metric=metric,
			age_categories=age_categories,
			sex_categories=sex_categories,
			outcome_categories=outcome_categories
		)
		cohort_results = cohort_int_output(
			bau_df=bau_df,
			run_id=run_id,
			base_path=base_path,
			metric=metric,
			age_categories=age_categories,
			sex_categories=sex_categories,
			outcome_categories=outcome_categories
		)
		write_output(
			base_path=base_path,
			run_id=run_id,
			metric=metric,
			int_type="period",
			results=period_results,
		)
		write_output(
			base_path=base_path,
			run_id=run_id,
			metric=metric,
			int_type="cohort",
			results=cohort_results,
		)


def make_output_files(runs, base_path, metrics, age_categories, sex_categories, outcome_categories):
	"""
	Loops through each simulation runs and produces output files suitable for reading
	by front-end.

	Parameters:
	* runs (list): List of runs to process. Elements must correspond to names 
	of files inside the folder defined by 'base_path'
	* base_path (str): Path to 'runs' folder
	* metrics (list): list of metrics targeted by intervention, i.e. 'incidence',
	'disability', and 'mortality'
	* age_categories (list): list of dictionaries specified start- and eng-age of 
	interventions. Of form: [{start_age: ..., end_age: ...}, {...}]
	* sex_categories (list): list of sexes.
	* outcome_categories (list): list of simulation outcomes, i.e. 'HALY', 'total_spent', 
	or 'total_income'

	Returns:
	None
	"""
	print("Formatting data ...")
	for run_id in tqdm(runs):
		process_run(
			run_id=run_id,
			base_path=base_path,
			metrics=metrics,
			age_categories=age_categories,
			sex_categories=sex_categories,
			outcome_categories=outcome_categories
		)


# make_output_files(
# 	runs=[*range(0,10)],
# 	base_path="data/runs",
# 	metrics=["incidence", "mortality", "disability"],
# 	age_categories=[
# 		{"age_start": 0, "age_end": 14},
# 		{"age_start": 15, "age_end": 24},
# 		{"age_start": 25, "age_end": 44},
# 		{"age_start": 45, "age_end": 64},
# 		{"age_start": 65, "age_end": 84},
# 		{"age_start": 85, "age_end": 110},
# 		{"age_start": 85, "age_end": 110},
# 	],
# 	sex_categories=["male", "female"],
# 	outcome_categories=["HALY", "total_spent", "total_income"]
# )

# print("Finished")