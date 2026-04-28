********************************************************************************
**** WRU Zip Extension Method - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 03/25/2026
Notes:
- PPP-specific counterpart to WRU_merge.do
- Uses fintech (fintech==1) instead of party DEM coding
*/


use "${dta}/PPP_clean.dta", clear


rename last_name lastname
rename first_name firstname
rename race_code race
rename zip_code zipcode
rename lastname surname

replace surname=strproper(surname)
replace firstname=strproper(firstname)

replace surname=upper(surname)

rename zipcode zcta5


merge m:m surname zcta5 using "${dta}/PPP_wru_interim_prediction.dta", nogen



replace race= "Unknown/Unreported" if race==""

** replace race for hispanic
replace race="Hispanic" if  ethnic_code=="HL"

** Do counts depending on the prediction

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


rename pred_whi predwhi
rename pred_bla predbla
rename pred_his predhis
rename pred_asi predasi
rename pred_oth predoth

gen predicted_race=""
replace predicted_race="White" if predwhi>predbla & predwhi>predhis & predwhi>predasi & predwhi>predoth
replace predicted_race="Black" if predbla>predwhi & predbla>predhis & predbla>predasi & predbla>predoth
replace predicted_race="Asian" if predasi>predbla & predasi>predhis & predasi>predwhi & predasi>predoth
replace predicted_race="Hispanic" if predhis>predbla & predhis>predwhi & predhis>predasi & predhis>predoth
replace predicted_race="Other" if predoth>predbla & predoth>predhis & predoth>predasi & predoth>predwhi


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


foreach var of varlist count_White_white count_White_asian count_White_black count_White_hispanic count_White_other ///
count_Asian_white count_Asian_asian count_Asian_black count_Asian_hispanic count_Asian_other ///
count_Black_white count_Black_asian count_Black_black count_Black_hispanic count_Black_other ///
count_Hispanic_white count_Hispanic_asian count_Hispanic_black count_Hispanic_hispanic count_Hispanic_other ///
count_Other_white count_Other_asian count_Other_black count_Other_hispanic ///
count_Other_other black white asian hispanic fintech_white fintech_black fintech_asian fintech_hispanic{

	rename `var' wru_`var'

}


save "${ans}/PPP_wru.dta", replace
