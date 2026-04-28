********************************************************************************
**** Racial Disparity all raw data - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 03/26/2026
Notes:
- PPP-specific counterpart to Race_disparity.do
- Uses fintech (fintech==1) instead of party DEM coding
*/


use "${dta}/PPP_clean.dta", clear


rename race_code race
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


gen black=0
replace black=1 if race_grouped=="Black"

gen white=0
replace white=1 if race_grouped=="White"

gen asian=0
replace asian=1 if race_grouped=="Asian"

gen hispanic=0
replace hispanic=1 if race_grouped=="Hispanic"

gen other=0
replace other=1 if race_grouped=="Other"


gen fintech_white=0
replace fintech_white=1 if race_grouped=="White" & fintech==1

gen fintech_black=0
replace fintech_black=1 if race_grouped=="Black" & fintech==1

gen fintech_asian=0
replace fintech_asian=1 if race_grouped=="Asian" & fintech==1

gen fintech_hispanic=0
replace fintech_hispanic=1 if race_grouped=="Hispanic" & fintech==1


egen total_observations=count(last_name)
egen total_black=total(black)
egen total_white=total(white)
egen total_hispanic=total(hispanic)
egen total_asian=total(asian)
egen total_other=total(other)
egen total_fintech_white=total(fintech_white)
egen total_fintech_black=total(fintech_black)
egen total_fintech_hispanic=total(fintech_hispanic)
egen total_fintech_asian=total(fintech_asian)


keep total_*
duplicates drop total_*, force
compress

save "${ans}/PPP_race_disparity.dta", replace
