********************************************************************************
************ PPP Birdie Method (Fintech Target)
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 03/25/2026
Notes:
- PPP-specific counterpart to birdie_clean.do
- Uses fintech (0/1) instead of party registration (DEM/other)
*/

* Upload data
use "${processed}/PPP_clean.dta", clear

rename last_name lastname
rename first_name firstname
rename race_code race
rename zip_code zipcode

compress

rename lastname surname

replace surname=strproper(surname)
replace firstname=strproper(firstname)

gen fintech_reg = .
replace fintech_reg = 1 if fintech==1
replace fintech_reg = 0 if fintech!=1 & fintech<.

order zipcode surname fintech_reg
keep zipcode surname fintech_reg

compress 

save "${method_inputs}/PPP_birdie_interim.dta", replace
