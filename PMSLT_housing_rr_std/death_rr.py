
import pandas as pd
import numpy as np
import json

def get_age_ses_acmr(
    df, 
    age_cat,
    ses_strata, 
    year
    ):
    '''
    Returns acmr for an age-SES sub-group, for a given year. Age refers
    to age in future years. I.e., inputing age_cat = 20-25 will return the
    acmr for those aged 20-25 in the year specified by the 'year' parameter.
    * df (pandas dataframe): dataframe to search (either int or bau)
    * age_cat (object): object of form {"start_age": int, "end_age": int}
    * ses_strata (str): SES strata to look up
    * year (int): year for which acmr is calculated.
    for, i.e. [2020, 2100]. Boundaries inclusive. Default is full sample.
    '''
    df = df.loc[
            (df["age"].between(age_cat["start_age"], age_cat["end_age"])) &
            (df["strata"] == ses_strata) &
            (df["year"] == year)
        ]
    deaths = df["deaths"].sum() 
    population = df["population"].sum() 
    if population > 0:
        return (deaths/population)
    else:
        return 0



def compute_age_std_rr(
    num_runs, 
    years
    ):
    ''' 
    Computes the ratio of acmr risk difference (RD) in BAU and intervention,
    were acmr risk difference is given by acmr inSES1 (most deprived) minus 
    acmr in SES5 (least deprived). Looks for runs in 'PMSLT_housing_rr_std/runs'. 
    Writes to output_rd.csv. 
    * num_runs (int): number of simulations to compute uncertainty over
    * years (list): list of years for which RD-ratio will be calcualted.
    for, i.e. [[2020, 2040], [2020, 2060]]. Boundaries inclusive. Default is full sample.
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
    runs = [*range(0,num_runs)] 
    results = {year: [] for year in years}
    base_dir = "./PMSLT_housing_rr_std"
    
    for run in runs:
        for year in years:
            bau_lifetable_df = pd.read_csv(f"{base_dir}/runs/{str(run)}/raw/output_lifetable_bau.csv")
            int_lifetable_df = pd.read_csv(f"{base_dir}/runs/{str(run)}/raw/output_lifetable_int.csv")

            df  = pd.DataFrame(age_cats)
            df["ses1_acmr"] = np.nan
            df["ses5_acmr"] = np.nan
            bau_acmr_df = df.copy()
            int_acmr_df = df.copy()

            for i in range(0, len(age_cats)):
                age_cat = age_cats[i]
                bau_acmr_df["ses1_acmr"] = get_age_ses_acmr(bau_lifetable_df, age_cat, "SES1", year) 
                bau_acmr_df["ses5_acmr"] = get_age_ses_acmr(bau_lifetable_df, age_cat, "SES5", year) 
                int_acmr_df["ses1_acmr"] = get_age_ses_acmr(int_lifetable_df, age_cat, "SES1", year) 
                int_acmr_df["ses5_acmr"] = get_age_ses_acmr(int_lifetable_df, age_cat, "SES5", year) 

            bau_rd = (bau_acmr_df["ses1_acmr"] * bau_acmr_df["who_weight"]).sum() - (bau_acmr_df["ses5_acmr"] * bau_acmr_df["who_weight"]).sum()
            int_rd = (int_acmr_df["ses1_acmr"] * int_acmr_df["who_weight"]).sum() - (int_acmr_df["ses5_acmr"] * int_acmr_df["who_weight"]).sum()

            results[year].append((int_rd / bau_rd) - 1)

            print(f"- year: {year}")
            print(f"- bau_rd: {bau_rd}")
            print(f"- int_rd: {int_rd}")
            print(f"- ratio: {(int_rd / bau_rd) - 1}")

        print(f"run ({run + 1}/{len(runs)}) ...\n") 

    output = {
            year: {
                "50th": round(np.percentile(np.array(result_array), 50), 4),
                "2.5th": round(np.percentile(np.array(result_array), 2.5), 4),
                "97.5th": round(np.percentile(np.array(result_array), 97.5), 4)
                }
            for year, result_array in results.items()
        }        

    print(
            "============================================\n" +
            "RESULTS\n" +
            "============================================\n" 
        )
    print(json.dumps(output, indent=4))

    output_df = pd.DataFrame(output).T
    output_df.to_csv(f"{base_dir}/output_acmr_rd.csv")

compute_age_std_rr(
        num_runs=1,
        years=[
            2021,
            2030,
            2050,
            2100,
        ]
    )


