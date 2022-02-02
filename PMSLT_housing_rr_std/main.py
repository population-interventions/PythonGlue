import pandas as pd
import numpy as np
import json

def get_age_ses_halys(
    df, 
    age_cat, 
    ses_strata, 
    time_horizon
    ):
    '''
    Returns sum of HALYs for an age-SES sub-group, for a given time horizon. Age refers
    to age in future years. I.e., inputing an age category of 20-25 will return the
    sum of HALYs for 20-25 y/o's in 2020, 2021, ..., 2XXX.
    * df (pandas dataframe): dataframe to search (either int or bau)
    * age_cat (object): object of form {"start_age": int, "end_age": int}
    * ses_strata (str): SES strata to look up
    * time_horzon (list): range of years to calculate age-standardisation
    for, i.e. [2020, 2100]. Boundaries inclusive. Default is full sample.
    '''
    df2 = df.loc[
            (df["age"].between(age_cat["start_age"], age_cat["end_age"])) &
            (df["strata"] == ses_strata) &
            (df["year"].between(time_horizon[0], time_horizon[1]))
        ]
    ses_halys_per_capita = df2["HALY"].sum() 
    return ses_halys_per_capita


def get_age_ses_person_years(
    df, 
    age_cat, 
    ses_strata,
    time_horizon
    ):
    '''
    Returns sum of person-years for an age-SES sub-group, for a given time horizon. 
    Age refers to age in future years. I.e., inputing an age category of 20-25 will
    return the sum of person-years for 20-25 y/o's in 2020, 2021, ..., 2XXX.
    * df (pandas dataframe): dataframe to search (either int or bau)
    * age_cat (object): object of form {"start_age": int, "end_age": int}
    * ses_strata (str): SES strata to look up
    * time_horzon (list): range of years to calculate age-standardisation
    for, i.e. [2020, 2100]. Boundaries inclusive. Default is full sample.
    '''
    df2 = df.loc[
            (df["age"].between(age_cat["start_age"], age_cat["end_age"])) &
            (df["strata"] == ses_strata) &
            (df["year"].between(time_horizon[0], time_horizon[1]))
        ]
    person_years = df2["person_years"].sum()
    return person_years


def compute_age_std_rr(
    num_runs, 
    time_horizon
    ):
    ''' 
    Computes age-standardised relative risk based on HALYs, comapring 
    SES1 (most deprived) to SES5 (least deprived). Looks for runs in
    'PMSLT_housing_rr_std/runs'. 
    * num_runs (int): number of simulations
    * time_horzon (list): range of years to calculate age-standardisation
    for, i.e. [2020, 2100]. Boundaries inclusive. Default is full sample.
    '''
    age_cats = [
            {"start_age": 0, "end_age": 4, "who_weight": 0.0886}, 
            {"start_age": 5, "end_age": 9, "who_weight": 0.0869}, 
            {"start_age": 10, "end_age": 14, "who_weight": 0.086}, 
            {"start_age": 15, "end_age": 19, "who_weight": 0.0847}, 
            {"start_age": 20, "end_age": 24, "who_weight": 0.0822}, 
            {"start_age": 25, "end_age": 29, "who_weight": 0.0793},
            {"start_age": 30, "end_age": 34, "who_weight": 0.0761},
            {"start_age": 35, "end_age": 39, "who_weight": 0.0715}, 
            {"start_age": 40, "end_age": 44, "who_weight": 0.0659}, 
            {"start_age": 45, "end_age": 49, "who_weight": 0.0604},
            {"start_age": 50, "end_age": 54, "who_weight": 0.0537}, 
            {"start_age": 55, "end_age": 59, "who_weight": 0.0455},
            {"start_age": 60, "end_age": 64, "who_weight": 0.0372}, 
            {"start_age": 65, "end_age": 69, "who_weight": 0.0296},
            {"start_age": 70, "end_age": 74, "who_weight": 0.0221}, 
            {"start_age": 75, "end_age": 79, "who_weight": 0.0152},
            {"start_age": 80, "end_age": 84, "who_weight": 0.0091}, 
            {"start_age": 85, "end_age": 110, "who_weight": 0.0064},

        ]
    sum_who_weights = 0
    for age_group in age_cats:
        sum_who_weights += age_group["who_weight"]
    ses_cats = {
            "SES5": {"age_std_haly_gain_per_1000py": [], "age_std_rr": []},
            "SES4": {"age_std_haly_gain_per_1000py": [], "age_std_rr": []},
            "SES3": {"age_std_haly_gain_per_1000py": [], "age_std_rr": []},
            "SES2": {"age_std_haly_gain_per_1000py": [], "age_std_rr": []},
            "SES1": {"age_std_haly_gain_per_1000py": [], "age_std_rr": []},
        }
    runs = [*range(0,num_runs)] 
    base_dir = "./PMSLT_housing_rr_std"
    
    for run in runs:
        bau_df = pd.read_csv(f"{base_dir}/runs/{str(run)}/raw/output_lifetable_bau.csv")
        int_df = pd.read_csv(f"{base_dir}/runs/{str(run)}/raw/output_lifetable_int.csv")

        for i in range(0, len(age_cats)):
            for ses_strata in ses_cats.keys():
                age_cats[i][f"bau_halys_{ses_strata}"] = get_age_ses_halys(bau_df, age_cats[i], ses_strata, time_horizon)
                age_cats[i][f"int_halys_{ses_strata}"] = get_age_ses_halys(int_df, age_cats[i], ses_strata, time_horizon)
                age_cats[i][f"haly_gain_per_1000py_{ses_strata}"] = 1000 * (
                        (age_cats[i][f"int_halys_{ses_strata}"] - age_cats[i][f"bau_halys_{ses_strata}"]) / 
                        get_age_ses_person_years(bau_df, age_cats[i], ses_strata, time_horizon)
                    )

        for ses_strata in ses_cats.keys():
            ses_cats[ses_strata]["age_std_haly_gain_per_1000py"].append(sum(
                    [(age_cat["who_weight"] * age_cat[f"haly_gain_per_1000py_{ses_strata}"])/sum_who_weights for age_cat in age_cats]
                ))
            ses_cats[ses_strata]["age_std_rr"].append((
                    ses_cats[ses_strata]["age_std_haly_gain_per_1000py"][-1] / ses_cats["SES5"]["age_std_haly_gain_per_1000py"][-1]
                ))
        print(f"run ({run + 1}/{len(runs)}) ...") 


    output = {
            key: {
                "age_std_haly_gain_per_1000py": {
                    "2.5th": np.percentile(np.array(value["age_std_haly_gain_per_1000py"]), 2.5),
                    "50th": np.percentile(np.array(value["age_std_haly_gain_per_1000py"]), 50),
                    "97.5th": np.percentile(np.array(value["age_std_haly_gain_per_1000py"]), 97.5),
                },
                "age_std_rr": {
                    "2.5th": np.percentile(np.array(value["age_std_rr"]), 2.5),
                    "50th": np.percentile(np.array(value["age_std_rr"]), 50),
                    "97.5th": np.percentile(np.array(value["age_std_rr"]), 97.5),
                }
            }
            for key, value in ses_cats.items()
        }

    print(json.dumps(output, indent=4))


compute_age_std_rr(
        num_runs=10,
        time_horizon=[2020,2030]
    )


