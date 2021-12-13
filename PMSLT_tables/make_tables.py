import pandas as pd
import numpy as np
from openpyxl import load_workbook


def make_tables(files):
	path_prefix= "PMSLT_tables/drawAgg"
	for file in files:
		df = pd.read_csv(f"{path_prefix}/{file['file_name']}")
		
		# Make population column
		df["Population"] = df[["Sex", "Strata"]].agg(" ".join, axis=1)
		df.loc[df["Population"] == "All All", "Population"] = "All"

		# Drop columns and rename
		df.drop(["BAU","Ban All Smoke 2023","Ban All Smoke and Vape 2023", "Sex", "Strata"], axis=1 ,inplace=True)
		df.rename({
			"Low Nicotine & Media": "Low nicotine + media",
			"Low Nicotine": "Low nicotine",
			"Retail": "Retail reduction",
			"Smokefree Generation": "Smokefree generation",
			"Combined" : "Combined interventions",
		},
		axis="columns", inplace=True)
		df.set_index(["Population", "Year"], inplace=True)

		# Split each column into "Estimate" and "Uncertainty"
		level_0_cols = df.columns
		df.columns = pd.MultiIndex.from_product([df.columns, ["Estimate"]])
		for column in level_0_cols:
			df[column, "Uncertainty"] = df[column, "Estimate"].str.split("(").map(lambda x: f"({x[1]}")
			df[column, "Estimate"] = df[column, "Estimate"].str.split("(").map(lambda x: float(x[0].strip().replace(",", "")))

		# Column ordering
		level_0_order = [
			"Low nicotine","Low nicotine + media","Retail reduction",
			"Smokefree generation","Combined interventions"
		]
		level_1_order = ["Estimate", "Uncertainty"]
		df = df.reindex(columns=level_0_order, level=0)
		df = df.reindex(columns=level_1_order, level=1)

		# Save file
		output_path = f"PMSLT_tables/output/{file['file_name']}"
		save_file(
			df=df,
			sheet_name=file["file_name"].replace("out_","").replace("year_year_", "").replace("discount","d").replace("_millions","")
		)

			
def save_file(df, sheet_name):
	output_path = "PMSLT_tables/output/output.xlsx"
	book = load_workbook(output_path)
	writer = pd.ExcelWriter(output_path, engine = 'openpyxl')
	writer.book = book
	writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
	# writer = pd.ExcelWriter("PMSLT_tables/output/output.xlsx", engine="openpyxl")
	print(sheet_name)
	df.to_excel(writer, sheet_name=sheet_name)
	writer.save()
	# writer.close()












file_names = [
	"out_deaths_year_year_0-111_discount_0.csv", 
	"out_HALY_year_year_0-111_discount_-0.02.csv",
	"out_HALY_year_year_0-111_discount_-0.03.csv",
	"out_HALY_year_year_0-111_discount_-0.05.csv",
	"out_HALY_year_year_0-111_discount_0.csv",
	"out_total_income_year_year_0-111_discount_-0.02_millions.csv",
	"out_total_income_year_year_0-111_discount_-0.03_millions.csv",
	"out_total_income_year_year_0-111_discount_-0.05_millions.csv",
	"out_total_income_year_year_0-111_discount_0_millions.csv",
	"out_total_spent_year_year_0-111_discount_-0.02_millions.csv",
	"out_total_spent_year_year_0-111_discount_-0.03_millions.csv",
	"out_total_spent_year_year_0-111_discount_-0.05_millions.csv",
	"out_total_spent_year_year_0-111_discount_0_millions.csv",
]

files = [
	{"file_name": "out_deaths_year_year_0-111_discount_0.csv", "title": "deaths_discount_0"}, 
	{"file_name": "out_HALY_year_year_0-111_discount_-0.02.csv", "title": "HALYS_discount_0.02"}, 
	{"file_name": "out_HALY_year_year_0-111_discount_-0.03.csv", "title": "HALYS_discount_0.03"}, 
	{"file_name": "out_HALY_year_year_0-111_discount_-0.05.csv", "title": "HALYS_discount_0.05"}, 
	{"file_name": "out_HALY_year_year_0-111_discount_0.csv", "title": "HALYS_discount_0"}, 
	{"file_name": "out_total_income_year_year_0-111_discount_-0.02_millions.csv", "title": "income_discount_0.02"}, 
	{"file_name": "out_total_income_year_year_0-111_discount_-0.03_millions.csv", "title": "income_discount_0.03"}, 
	{"file_name": "out_total_income_year_year_0-111_discount_-0.05_millions.csv", "title": "income_discount_0.05"}, 
	{"file_name": "out_total_income_year_year_0-111_discount_0_millions.csv", "title": "income_discount_0"}, 
	{"file_name": "out_total_spent_year_year_0-111_discount_-0.02_millions.csv", "title": "expenditure_discount_0.02"}, 
	{"file_name": "out_total_spent_year_year_0-111_discount_-0.03_millions.csv", "title": "expenditure_discount_0.03"}, 
	{"file_name": "out_total_spent_year_year_0-111_discount_-0.05_millions.csv", "title": "expenditure_discount_0.05"}, 
	{"file_name": "out_total_spent_year_year_0-111_discount_0_millions.csv", "title": "expenditure_discount_0"}, 
]


make_tables(files)
print("done")