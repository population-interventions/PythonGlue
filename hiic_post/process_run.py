from src.main import process_run
import sys

run_id = int(sys.argv[1])

process_run(
	run_id=run_id,
	base_path="../../../pmslt/results/hiic/runs",
	metrics=["incidence", "mortality", "disability"],
	age_categories=[
		{"age_start": 0, "age_end": 14},
		{"age_start": 15, "age_end": 24},
		{"age_start": 25, "age_end": 44},
		{"age_start": 45, "age_end": 64},
		{"age_start": 65, "age_end": 84},
		{"age_start": 85, "age_end": 110},
		{"age_start": 85, "age_end": 110},
	],
	sex_categories=["male", "female"],
	outcome_categories=["HALY", "total_spent", "total_income"]
)

print("done")