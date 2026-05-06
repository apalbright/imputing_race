********************************************************************************
**** Zip Code Method - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 03/26/2026
Notes:
- PPP-specific counterpart to zip.do
- Uses the national NHGIS ZCTA file directly, not the NC-only ZIP file
- Uses fintech (fintech==1) instead of party DEM coding
*/


tempfile zcta_lookup


******************** ZIPCODE LOOKUP
* Required NHGIS input is tracked in GitHub under Data/raw/geo/.
* Tracked support input:
* Data/raw/geo/nhgis0002_ds267_20235_zcta.csv
import delimited "${support}/nhgis0002_ds267_20235_zcta.csv", clear

compress

rename asoae001 total_pop
rename asoae003 white_pop
rename asoae004 black_pop
rename asoae005 american_indian_pop
rename asoae006 asian_pop
rename asoae007 pacific_islander_pop
rename asoae008 other_pop
rename asoae009 two_pop
rename asoae010 two_2_pop
rename asoae011 two_3_pop
rename asoae012 hispanic_pop

keep geo_id total_pop white_pop black_pop american_indian_pop asian_pop pacific_islander_pop other_pop two_pop two_2_pop two_3_pop hispanic_pop

compress

egen total_asian=rowtotal(asian_pop pacific_islander_pop)
egen total_other=rowtotal(other_pop two* american_indian_pop)

gen percent_white=(white_pop/total_pop)*100
gen percent_black=(black_pop/total_pop)*100
gen percent_asian=(total_asian/total_pop)*100
gen percent_hispanic=(hispanic_pop/total_pop)*100
gen percent_other=(total_other/total_pop)*100

gen zip_code = substr(geo_id, -5, 5)
destring zip_code, replace

keep zip_code percent_*
duplicates drop zip_code, force

rename zip_code zipcode
save `zcta_lookup'


******************** PPP DATA
use "${processed}/PPP_clean.dta", clear

rename race_code race
rename zip_code zipcode

destring zipcode, replace force

replace race= "Unknown/Unreported" if race==""
replace race="Hispanic" if ethnic_code=="HL"

keep zipcode race ethnic_code fintech


merge m:1 zipcode using `zcta_lookup'
keep if _m==3
drop _m


gen final_race=""
replace final_race="black" if percent_black>percent_white & percent_black>percent_hispanic & percent_black>percent_asian & percent_black>percent_other
replace final_race="white" if percent_white>percent_black & percent_white>percent_hispanic & percent_white>percent_asian & percent_white>percent_other
replace final_race="hispanic" if percent_hispanic>percent_white & percent_hispanic>percent_black & percent_hispanic>percent_asian & percent_hispanic>percent_other
replace final_race="asian" if percent_asian>percent_white & percent_asian>percent_hispanic & percent_asian>percent_black & percent_asian>percent_other
replace final_race="NA" if percent_other>percent_white & percent_other>percent_hispanic & percent_other>percent_black & percent_other>percent_asian


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
replace race_predicted_grouped="Other" if final_race=="NA"


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

	rename `var' zip_`var'

}


save "${ans}/PPP_zip.dta", replace
