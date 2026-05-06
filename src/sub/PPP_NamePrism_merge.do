
clear all
set more off

/*
Created by: Weiran
Date: 03/31/2026
Notes:
- PPP-specific counterpart to NamePrism_merge.do
- Uses fintech (fintech==1) instead of party DEM coding
*/


* Upload data

import delimited "${method_inputs}/PPP_NamePrism.csv", varnames(1) clear
gen N=_n
replace N=N-1
keep N fullname
tempfile t1
save `t1'

import delimited "${predictions}/PPP_NamePrism_res.csv", clear
rename a N

merge 1:1 N using `t1', nogen

compress



split b, parse(,)
split c, parse(,)
split d, parse(,)
split e, parse(,)
split f, parse(,)
split g, parse(,)

rename b2 more_2_race
rename c2 hispanic
rename d2 asian
rename e2 black
rename f2 american_indian_alaskan
rename g2 white

drop b1 c1 d1 e1 f1 g1

gen predicted=""

drop b c d e f g

destring more_2_race, replace
destring hispanic, replace
destring asian, replace
destring black, replace
destring american_indian_alaskan, replace
destring white, replace



replace predicted="W" if white>more_2_race & white>hispanic & white>asian & white>black & white> american_indian_alaskan
replace predicted="A" if asian>more_2_race & asian>hispanic & asian>white & asian>black & asian> american_indian_alaskan
replace predicted="H" if hispanic>more_2_race & hispanic>asian & hispanic>white & hispanic>black & hispanic> american_indian_alaskan
replace predicted="B" if black>more_2_race & black>asian & black>white & black>hispanic & black> american_indian_alaskan
replace predicted="O" if american_indian_alaskan>more_2_race & american_indian_alaskan>asian & american_indian_alaskan>white & american_indian_alaskan>hispanic & american_indian_alaskan> black
replace predicted="O" if more_2_race>american_indian_alaskan & more_2_race>asian & more_2_race>white & more_2_race>hispanic & more_2_race> black
compress

keep fullname predicted
compress


save "${predictions}/PPP_Nameprism_Python.dta", replace


*********************************************************************************
** Now match the outcomes from Python code to the above data and verify that how correct the predictions are
********************
use "${processed}/PPP_clean.dta", clear


replace first_name=strupper(first_name)
replace last_name=strupper(last_name)

gen name = first_name + " " + last_name

replace name=stritrim(name)


rename name fullname


merge m:m fullname using "${predictions}/PPP_Nameprism_Python.dta"
keep if _m==3
 drop _m

replace race_code= "Unknown/Unreported" if race_code==""

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
replace predicted_race="White" if predicted=="W"
replace predicted_race="Black" if predicted=="B"
replace predicted_race="Asian" if predicted=="A"
replace predicted_race="Hispanic" if predicted=="H"
replace predicted_race="Other" if predicted=="O"

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


	rename `var' Nprism_`var'

}


save "${ans}/PPP_Nameprism.dta", replace
