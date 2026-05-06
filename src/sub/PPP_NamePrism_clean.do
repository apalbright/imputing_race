********************************************************************************
**** NamePrism Method - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 03/31/2026
Notes:
- PPP-specific counterpart to NamePrism_clean.do
- Splits PPP data into two halves for NamePrism API batches
*/


* Upload data

use "${processed}/PPP_clean.dta", clear


replace first_name=strupper(first_name)
replace last_name=strupper(last_name)

gen name = first_name + " " + last_name

replace name=stritrim(name)


rename name fullname

keep fullname

*** Single batch export for NamePrism API

compress
export delimited using "${method_inputs}/PPP_NamePrism.csv", replace
