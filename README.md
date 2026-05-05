# Replication Package for "Imputing Race"

This repository contains replication materials for the paper "Imputing Race" 
- Paper authors: [Alex Albright](https://www.albrightalex.com/) and [Juliana Gamboa-Arbelaez](https://sites.google.com/view/juliana-gamboa-arbelaez/home)
- Paper date: May 2026

---


### Raw Data

1. **PPP data**
   - Data source: [US Small Business Administration (SBA) - FOIA release (last updated: 10/21/24)](https://data.sba.gov/dataset/ppp-foia)
   - Raw data exceeds GitHub's file size limits, so it must be downloaded directly from SBA and placed in `Data/raw/`
      - *Raw files are also backed up [on OSF](https://osf.io/bq7n8) in case the SBA link breaks or data is removed*

2. **ZIP code-level race composition data**
   - The PPP ZIP benchmark requires `nhgis0002_ds267_20235_zcta.csv` in `Data/`.
     This NHGIS extract is not included in GitHub; users must download the matching NHGIS ZCTA extract and save/rename it to `Data/nhgis0002_ds267_20235_zcta.csv` before running the ZIP benchmark.

3. **ZIP-to-tract crosswalk**
   - The PPP BIFSG workflow uses `ZIP_TRACT_122025.xlsx` or `ZIP_TRACT_122025_bestres.dta` in `Data/`.

All other files in `Data/` are cleaned and processed datasets.

---

### Instructions to replicate everything

0. Run `src/00_clean_raw_PPP.py` *(Python)* to merge raw PPP files, filter person names, parse borrower names, and generate cleaned data: `Data/PPP_person_names_filtered.csv` and `Data/PPP_person_names_final.csv`
1. Run `src/01_clean_prep_PPP.do` *(Stata)* to set paths, clean the parsed PPP borrower file, and set up data for all imputation methods
2. Run `src/02_predict_PPP.Rmd` *(R)* to run all imputation methods that use R *(surname, BISG, BIFSG, BIRDiE)*
3. To generate ZRP results,
   - upload the full replication package into google drive under Colab notebooks files
   - run `src/03_ZRP_PPP.ipynb` *(Python notebook)*
   - it writes `Data/PPP_results_interim_ZRP.csv`, save it locally to `Data` and leave the Colab environment
4. To generate NamePrism results,
   - request an API key for running NamePrism [here](https://www.name-prism.com/api)
   - add the API key to `src/sub/PPP_NamePrism_predict.py`
   - run `python src/04_NamePrism_predict_PPP.py` *(Python)*
5. Run `src/05_merge_all_methods_PPP.do` *(Stata)* to merge all imputation method results and yield PPP evaluation files in `Results/Plots`
6. Run `src/06_make-graphs_PPP.Rmd` *(R)* to create all PPP figures
7. Run `src/07_rank_tables_PPP.R` *(R)* to create the PPP rank table CSV in `Results/Plots` and the table figure in `Results/Plots/Figs`

---


### Software requirements

Code was run with the following software and package versions:

- Stata version MP 17.0
- R version 4.1+
    -    Haven
    -    Dplyr
    -    Tidyverse
    -    WRU
    -    Birdie
    -    Future
    -    Future.callr
    -    GT
    -    ggthemes
    -    grafify
    -    patchwork
- Python version 3.11.7 for the PPP NamePrism script
    -    Numpy
    -    Pandas
    -    Nameparser
    -    Requests
- Python version 3.7.7 environment for PPP ZRP
    -    zrp

### Runtime

- run for `00_clean_raw_PPP.py`: several min
- run for `01_clean_prep_PPP.do`: a few min
- run for `02_predict_PPP.Rmd`: several min
- run for `src/sub/PPP_ZRP_predict.py`: used A100 GPU in Google colab, 1.5 hours
- run for `04_NamePrism_predict_PPP.py`: about 0.9 second per name, 70 hours in total
- run for `05_merge_all_methods_PPP.do`: 1-2 min
- run for `06_make-graphs_PPP.Rmd`: 1-2 min
- run for `07_rank_tables_PPP.R`: short

### Note on generated files

- Stata creates `.log` files automatically when scripts are run in batch mode, for example with `stata-mp -b do ...`. These logs are not required for replication and can be deleted after the run.
- Python `__pycache__/` folders and `.pyc` files are runtime caches and are not required.
