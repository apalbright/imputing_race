********************************************************************************
**** Last Name Method - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 03/26/2026
Notes:
- PPP-specific counterpart to last_name_merge.do
- Uses PPP-specific surname predictions from results_interim_lastname_PPP.dta
- Uses fintech (fintech==1) instead of party DEM coding
*/

use "${processed}/PPP_clean.dta", clear


rename last_name lastname
rename first_name firstname
rename race_code race
capture confirm file "${predictions}/results_interim_lastname_PPP.dta"
if _rc!=0 {
	di as error "Missing PPP surname prediction lookup: ${predictions}/results_interim_lastname_PPP.dta"
	exit 601
}

merge m:m lastname using "${predictions}/results_interim_lastname_PPP.dta"
keep if _m==3
drop _m


gen final_race= likely_race
replace race= "Unknown/Unreported" if race==""
replace race="Hispanic" if ethnic_code=="HL"


gen race_grouped=""
replace race_grouped="White" if race=="W"
replace race_grouped="Asian" if race=="A"
replace race_grouped="Hispanic" if race=="Hispanic"
replace race_grouped="Black" if race=="B"
replace race_grouped="Other" if race=="I"
replace race_grouped="Other" if race=="M"
replace race_grouped="Other" if race=="O"
replace race_grouped="Other" if race=="U"
replace race_grouped="Asian" if race=="P"


gen count_asian=1 if race_grouped=="Asian"
gen count_black=1 if race_grouped=="Black"
gen count_white=1 if race_grouped=="White"
gen count_hispanic=1 if race_grouped=="Hispanic"
gen count_other=1 if race_grouped=="Other"


gen race_predicted_grouped=""
replace race_predicted_grouped="White" if final_race=="white"
replace race_predicted_grouped="Hispanic" if final_race=="hispanic, white"
replace race_predicted_grouped="Hispanic" if final_race=="hispanic"
replace race_predicted_grouped="Black" if final_race=="black, white"
replace race_predicted_grouped="Black" if final_race=="black"
replace race_predicted_grouped="Asian" if final_race=="asian, white"
replace race_predicted_grouped="Asian" if final_race=="asian"
replace race_predicted_grouped="Asian" if final_race=="asian, hispanic"
replace race_predicted_grouped="Other" if final_race=="american_indian"
replace race_predicted_grouped="Other" if final_race=="2races"
replace race_predicted_grouped="Other" if final_race=="other"


gen Rcount_asian=1 if race_predicted_grouped=="Asian"
gen Rcount_black=1 if race_predicted_grouped=="Black"
gen Rcount_white=1 if race_predicted_grouped=="White"
gen Rcount_hispanic=1 if race_predicted_grouped=="Hispanic"
gen Rcount_other=1 if race_predicted_grouped=="Other"


foreach name in "White" "Asian" "Black" "Hispanic" "Other" {

	gen count_`name'_white=1 if race_grouped=="`name'" & race_predicted_grouped=="White"
	gen count_`name'_asian=1 if race_grouped=="`name'" & race_predicted_grouped=="Asian"
	gen count_`name'_black=1 if race_grouped=="`name'" & race_predicted_grouped=="Black"
	gen count_`name'_hispanic=1 if race_grouped=="`name'" & race_predicted_grouped=="Hispanic"
	gen count_`name'_other=1 if race_grouped=="`name'" & race_predicted_grouped=="Other"

}


** Race Disparity

gen black=0
replace black=1 if race_predicted_grouped=="Black"

gen white=0
replace white=1 if race_predicted_grouped=="White"

gen asian=0
replace asian=1 if race_predicted_grouped=="Asian"

gen hispanic=0
replace hispanic=1 if race_predicted_grouped=="Hispanic"


gen fintech_white=0
replace fintech_white=1 if race_predicted_grouped=="White" & fintech==1

gen fintech_black=0
replace fintech_black=1 if race_predicted_grouped=="Black" & fintech==1

gen fintech_asian=0
replace fintech_asian=1 if race_predicted_grouped=="Asian" & fintech==1

gen fintech_hispanic=0
replace fintech_hispanic=1 if race_predicted_grouped=="Hispanic" & fintech==1


collapse (sum) Rcount_* count_* black white asian hispanic fintech*


foreach var of varlist count_White_white count_White_asian count_White_black count_White_hispanic count_White_other ///
count_Asian_white count_Asian_asian count_Asian_black count_Asian_hispanic count_Asian_other ///
count_Black_white count_Black_asian count_Black_black count_Black_hispanic count_Black_other ///
count_Hispanic_white count_Hispanic_asian count_Hispanic_black count_Hispanic_hispanic count_Hispanic_other ///
count_Other_white count_Other_asian count_Other_black count_Other_hispanic ///
count_Other_other black white asian hispanic fintech_white fintech_black fintech_asian fintech_hispanic {

	rename `var' lastname_`var'

}


save "${ans}/PPP_lastname.dta", replace
