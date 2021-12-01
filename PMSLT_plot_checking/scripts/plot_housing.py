import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import os


def getFutureRatesForAgeGroup(
	age_grp,
	disease_name,
	disease_data_dir,
	output_dir
):
	main_df = pd.read_csv(f"{disease_data_dir}/{disease_name}.csv")

	main_df = main_df.loc[
		(main_df["age"] == age_grp)
	]
	
	fig, axes = plt.subplots(figsize=[12,9], nrows=3, ncols=2, sharex=True)
	fig.suptitle(disease_name,fontsize=20)

	idx=0
	for rate in ["prev", "i", "f"]:
		y_lim = 0

		for sex in ["male", "female"]:
			# Assign subplot index
			row_idx = math.floor(idx/2) 
			col_idx = idx%2 

			# Pull out year column for merging subsequent SES dataframes
			plot_df = main_df.copy() 
			plot_df = plot_df.loc[
				(plot_df["strata"] == "SES1") &
				(plot_df["sex"] == "male")
			]
			plot_df = plot_df[["year"]]

			for strata in ["SES1", "SES2", "SES3", "SES4", "SES5"]:
				temp_df = main_df.copy()
				temp_df = temp_df.loc[
					(temp_df["strata"] == strata) &
					(temp_df["sex"] == sex)
				]
				temp_df = temp_df[["year",rate]]
				temp_df.rename(columns={rate: strata}, inplace =True)

				plot_df = plot_df.merge(temp_df, on="year", how="inner")

			plot_df.plot(ax=axes[row_idx, col_idx], x="year", y=["SES1", "SES2", "SES3", "SES4", "SES5"], legend=None)

			y_lim = max(y_lim, plot_df[["SES1", "SES2", "SES3", "SES4", "SES5"]].max().max()*1.5)

			axes[row_idx, col_idx].set_title(f"{rate}: {sex} aged {age_grp}")
			axes[row_idx, col_idx].grid()
			axes[row_idx, col_idx].legend(loc="upper right")
			
			idx += 1

		if y_lim !=0 :
			axes[row_idx, col_idx].set_ylim(0, y_lim)
			axes[row_idx, col_idx -1].set_ylim(0, y_lim)
		
	plt.tight_layout()
	fig.subplots_adjust(bottom=0.1) 
	# fig.legend(labels=["SES1", "SES2", "SES3", "SES4", "SES5"], loc="lower center", ncol=5)


	if not os.path.exists(f"{output_dir}/{disease_name}"):
		os.makedirs(f"{output_dir}/{disease_name}")
	plt.savefig(f"{output_dir}/{disease_name}/{disease_name}_{age_grp}.png")
	
	plt.cla()
	plt.close()



disease_names = ["ihd", "copd", "stroke", "atrial_fib_and_flutter", "chronic_kidney_disease"]
age_grps = [20, 40, 60, 80]

idx=1
for disease_name in disease_names:
	for age_grp in age_grps:
		print(f"Plotting {idx}/{len(disease_names)*len(age_grps)}...\n- disease: {disease_name}\n- age: {age_grp} ")
		print("------------------------------------")
		getFutureRatesForAgeGroup(
			age_grp=age_grp,
			disease_name=disease_name,
			disease_data_dir="PMSLT_plot_checking/data/housing_output/raw/bau_disease",
			output_dir="PMSLT_plot_checking/plots/housing"
		)
		idx+=1


print("done")