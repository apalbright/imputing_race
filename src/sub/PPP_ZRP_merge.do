********************************************************************************
**** ZRP Method - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 03/31/2026
Notes:
- PPP-specific counterpart to ZRP_merge.do
- Uses fintech (fintech==1) instead of party DEM coding
*/


clear
import delimited "${predictions}/PPP_results_interim_ZRP.csv"

capture confirm numeric variable zip_code
if _rc == 0 {
	gen str5 zip_code_str = string(zip_code, "%05.0f")
	drop zip_code
	rename zip_code_str zip_code
}
else {
	replace zip_code = substr("00000" + trim(zip_code), -5, 5)
}

keep first_name middle_name last_name zip_code race_proxy
compress


save "${predictions}/PPP_results_interim_ZRP.dta", replace


*********************************************************************************
** Now match the outcomes from Python code to the above data and verify that how correct the predictions are
********************
use "${processed}/PPP_clean.dta", clear


recast  str146 last_name, force
recast  str143 first_name, force
recast  str165 middle_name, force


merge m:m first_name middle_name last_name zip_code using "${predictions}/PPP_results_interim_ZRP.dta"


 ** replace race for hispanic
replace race_code="Hispanic" if  ethnic_code=="HL"

** Do counts depending on the wrong prediction
gen race_grouped=""
replace race_grouped="White" if race_code=="W"
replace race_grouped="Asian" if race_code=="A"
replace race_grouped="Hispanic" if race_code=="Hispanic"
replace race_grouped="Black" if race_code=="B"
replace race_grouped="Other" if race_code=="I"
replace race_grouped="Other" if race_code=="M"
replace race_grouped="Other" if race_code=="O"
replace race_grouped="Other" if race_code=="U"
replace race_grouped="Asian" if race_code=="P"


gen predicted_race=""
replace predicted_race="White" if race_proxy=="WHITE"
replace predicted_race="Black" if race_proxy=="BLACK"
replace predicted_race="Asian" if race_proxy=="AAPI"
replace predicted_race="Hispanic" if race_proxy=="HISPANIC"
* American Indian or Native American
replace predicted_race="Other" if race_proxy=="AIAN"

gen Rcount_asian=1 if predicted_race=="Asian"
gen Rcount_black=1 if predicted_race=="Black"
gen Rcount_white=1 if predicted_race=="White"
gen Rcount_hispanic=1 if predicted_race=="Hispanic"
gen Rcount_other=1 if predicted_race=="Other"


foreach name in "White" "Asian" "Black" "Hispanic" "Other" {


	gen count_`name'_white=1 if race_grouped=="`name'" & predicted_race=="White"
	gen count_`name'_asian=1 if race_grouped=="`name'" & predicted_race=="Asian"
	gen count_`name'_black=1 if race_grouped=="`name'" & predicted_race=="Black"
	gen count_`name'_hispanic=1 if race_grouped=="`name'" & predicted_race=="Hispanic"
	gen count_`name'_other=1 if race_grouped=="`name'" & predicted_race=="Other"

}


** Race Disparity

gen black=0
replace black=1 if predicted_race=="Black"

gen white=0
replace white=1 if predicted_race=="White"

gen asian=0
replace asian=1 if predicted_race=="Asian"

gen hispanic=0
replace hispanic=1 if predicted_race=="Hispanic"


gen fintech_white=0
replace fintech_white=1 if predicted_race=="White" & fintech==1

gen fintech_black=0
replace fintech_black=1 if predicted_race=="Black" & fintech==1

gen fintech_asian=0
replace fintech_asian=1 if predicted_race=="Asian" & fintech==1

gen fintech_hispanic=0
replace fintech_hispanic=1 if predicted_race=="Hispanic" & fintech==1



collapse (sum) Rcount_* count_* black white asian hispanic fintech*


foreach var of varlist count_White_white count_White_asian count_White_black	count_White_hispanic count_White_other	///
count_Asian_white count_Asian_asian	count_Asian_black	count_Asian_hispanic	count_Asian_other	///
count_Black_white count_Black_asian	count_Black_black	count_Black_hispanic	count_Black_other	///
count_Hispanic_white count_Hispanic_asian	count_Hispanic_black	count_Hispanic_hispanic	count_Hispanic_other	///
count_Other_white count_Other_asian	count_Other_black	count_Other_hispanic	///
count_Other_other black	white asian hispanic fintech_white fintech_black fintech_asian fintech_hispanic {

	rename `var' ZRP_`var'

}

compress

save "${ans}/PPP_ZRP.dta", replace
