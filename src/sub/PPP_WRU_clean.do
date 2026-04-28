********************************************************************************
**** WRU Zip Extension Method - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 03/25/2026
Notes:
- PPP-specific counterpart to WRU_clean.do
- Uses observed state values (not fixed NC)
*/

* Upload data
capture confirm file "${dta}/PPP_clean.csv"
if _rc==0 {
	import delimited "${dta}/PPP_clean.csv", clear varnames(1)
}
else {
	use "${dta}/PPP_clean.dta", clear
}


rename last_name lastname
rename first_name firstname
rename race_code race
rename zip_code zipcode
rename lastname surname

replace surname=strproper(surname)
replace firstname=strproper(firstname)

capture confirm string variable state
if _rc tostring state, replace force
replace state = upper(trim(state))

order zipcode surname firstname state
keep zipcode surname firstname state

compress


save "${dta}/PPP_wru_interim.dta", replace
