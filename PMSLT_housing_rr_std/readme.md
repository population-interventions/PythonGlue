# PMSLT_housing_rr_std

Uses individual housings runs from HPC to calculates age-standardised relative risks using
HALYS gained by intervention in SES1 (per BAU-SES1 person-year), vs HALYS gained by SES5 in
BAU (per BAU-SES5 person-year) with 95% uncertainty interval.

## Formulas

#### Age-standardised HALYS gained

Calculated seperately for each socioeconomic strata, according to the formula below.

<!-- age*std_halys_gained = $\displaystyle\sum*{i=1}^{n} w*i$ \* $\frac{\text{halys_int}*{i} - \text{halys_bau}_{i}}{\text{person_years_bau}_{i}}$ -->
<img src="https://latex.codecogs.com/png.image?\dpi{110}&space;\bg_white&space;\textup{age\_std\_halys\_gained}=\sum_{i=1}^{n}w_i&space;\ast&space;\frac{\textup{halys\_int}_i&space;-&space;\textup{halys\_bau}_i}{\textup{person\_years\_bau}_i}&space;" title="\bg_white \textup{age\_std\_halys\_gained}=\sum_{i=1}^{n}w_i \ast \frac{\textup{halys\_int}_i - \textup{halys\_bau}_i}{\textup{person\_years\_bau}_i} " />

-   i = age-group
-   w = WHO weight for age-group

#### Age-standardised relative-risk

Calculated by dividing age-standardised HALYS gained by interevention in SES1 (most depreived) by
that in SES5 (least deprived).

<!-- age*std_rr = $\frac{\text{age_std_halys_gained}*{SES\text{-1}}}{\text{age_std_halys_gained}\_{SES\text{-5}}}$ -->
<img src="https://latex.codecogs.com/png.image?\dpi{110}&space;\bg_white&space;\textup{age\_std\_rr}=&space;\frac{\textup{age\_std\_halys\_gained}_{\textup{SES-1}}}{\textup{age\_std\_halys\_gained}_{\textup{SES-5}}}" title="\bg_white \textup{age\_std\_rr}= \frac{\textup{age\_std\_halys\_gained}_{\textup{SES-1}}}{\textup{age\_std\_halys\_gained}_{\textup{SES-5}}}" />

## Directory Structure

Runs should be placed in the directory as follows:

```
PMSLT_housing_rr_std
│
├── runs
│   ├── 0
│   │   ├── process
│   │   └── raw
│   │       ├── output_lifetable_bau.csv
│   │       └── output_lifetable_int.csv
│   ├── 1
│   ├── ...
│   └── n
├── main.py
└── readme.md
```
