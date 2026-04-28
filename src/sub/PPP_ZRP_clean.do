********************************************************************************
**** ZRP Method - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 03/31/2026
Notes:
- PPP-specific counterpart to ZRP_clean.do
- Uses actual state and address fields from PPP data (not hardcoded)
*/


* Upload data
use "${dta}/PPP_clean.dta", clear


keep last_name first_name middle_name zip_code state street_address house_number city

tostring zip_code, replace


replace zip_code="" if zip_code=="."


export delimited using "${dta}/PPP_ZRP_interim.csv", replace
