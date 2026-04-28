********************************************************************************
**** Last Name Method - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 03/26/2026
Notes:
- PPP-specific counterpart to last_name_clean.do
- Writes a PPP-specific surname interim file for PPP_last_name_predict.Rmd
*/


* Upload data

use "${dta}/PPP_clean.dta", clear

***With underlying BISG probabilities Zipcode
rename last_name lastname
rename first_name firstname


keep lastname firstname

order lastname firstname

compress


save "${dta}/lastname_interim_PPP.dta", replace
