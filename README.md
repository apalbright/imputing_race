# Replication Package for "Imputing Race"

This repository contains replication materials for the paper "Imputing Race" 
- Paper authors: [Alex Albright](https://www.albrightalex.com/) and [Juliana Gamboa-Arbelaez](https://sites.google.com/view/juliana-gamboa-arbelaez/home)
- Paper date: **May 2026**

---


### Raw Data

1. PPP data
   - Data source: [US Small Business Administration (SBA) - FOIA release (last updated: 10/21/24)](https://data.sba.gov/dataset/ppp-foia)
   - Raw data exceeds GitHub's file size limits, so it must be downloaded directly from SBA and placed in `Data/raw/`
      - *Raw files are also backed up [on OSF](https://osf.io/bq7n8) in case the SBA link breaks or data is removed*

2. ZIP code-level race composition data
   - The PPP ZIP benchmark uses the tracked support file `Data/support/nhgis0002_ds267_20235_zcta.csv`. Data source: [NHGIS](https://www.nhgis.org/)

3. ZIP-to-tract crosswalk
   - The PPP BIFSG workflow uses the tracked support files `Data/support/ZIP_TRACT_122025.xlsx` and `Data/support/ZIP_TRACT_122025_bestres.dta`. Data source: [HUD USER ZIP CODE CROSSWALK FILES](https://www.huduser.gov/portal/datasets/usps_crosswalk.html)


Data file structure:

```text
Data/raw                     downloaded raw PPP data
Data/interim/processed_PPP/  cleaned PPP, ready to test method
Data/interim/method_inputs/  method-specific input files
Data/interim/predictions/    method-specific prediction files
```

---

### Instructions to replicate everything

1. Run `src/00_clean_raw_PPP.py` *(Python)* to merge raw PPP files, filter person names, parse borrower names, and generate cleaned data
2. Run `src/01_clean_prep_PPP.do` *(Stata)* to set paths, clean the parsed PPP borrower file, and set up data for all imputation methods
3. Run `src/02_predict_PPP.Rmd` *(R)* to run all imputation methods that use R *(surname, BISG, BIFSG, BIRDiE)*
4. To generate *ZRP* results,
   - upload the full replication package into google drive under Colab notebooks files
   - run `src/03_ZRP_PPP.ipynb` *(Python notebook)*
   - it writes `Data/interim/predictions/PPP_results_interim_ZRP.csv`, save it locally to `Data/interim/predictions/` and leave the Colab environment
5. To generate *NamePrism* results,
   - request an API key for running NamePrism [here](https://www.name-prism.com/api)
   - add the API key to `src/sub/PPP_NamePrism_predict.py`
   - run `src/04_NamePrism_predict_PPP.py` *(Python)*
6. Run `src/05_merge_all_methods_PPP.do` *(Stata)* to merge all imputation method results
7. Run `src/06_make-graphs_PPP.Rmd` *(R)* to create all PPP figures (pngs)
8. Run `src/07_rank_tables_PPP.R` *(R)* to create the PPP rank table (csv)


---


### Software requirements

Code was run with the following software and package versions:

- Stata version MP 18.0
- R version 4.1
    - haven 2.5.4
    - foreign 0.8-90
    - predictrace 2.0.1
    - birdie 0.6.1
    - dplyr 1.1.4
    - remotes 2.5.0
    - wru 3.0.3
    - readr 2.1.5
    - stringr 1.5.2
    - purrr 1.1.0
    - future 1.67.0
    - future.callr 0.10.2
    - rmarkdown 2.29
    - here 1.0.2
    - tidyverse 2.0.0
    - gt 1.0.0
    - ggthemes 5.2.0
    - grafify 5.1.0
    - patchwork 1.3.2
    - zipWRUext2 October 2025 version
- Python version 3.11.7 for raw PPP cleaning and NamePrism scripts
    - nameparser 1.1.3
    - numpy 1.26.4
    - pandas 2.1.4
    - requests 2.32.5
    - time, os, subprocess, sys, pathlib, re, csv, shutil, warnings, pdb, collections, and urllib are from the Python 3.11.7 standard library
- Python version 3.7.7 environment for PPP ZRP
    - zrp 0.4.1

### Runtime

- run for `00_clean_raw_PPP.py`: 10 min
- run for `01_clean_prep_PPP.do`: 1-2 min
- run for `02_predict_PPP.Rmd`: 3-5 min
- run for `src/sub/PPP_ZRP_predict.py`: used A100 GPU in Google colab, 1.5 hours
- run for `04_NamePrism_predict_PPP.py`: about 0.9 second per name, 70 hours in total
- run for `05_merge_all_methods_PPP.do`: 1-2 min
- run for `06_make-graphs_PPP.Rmd`: 1-2 min
- run for `07_rank_tables_PPP.R`: 1-2 min

### Note on generated files

- Stata creates `.log` files automatically when scripts are run in batch mode, for example with `stata-mp -b do ...`. These logs are not required for replication and can be deleted after the run.
- Python `__pycache__/` folders and `.pyc` files are runtime caches and are not required.
