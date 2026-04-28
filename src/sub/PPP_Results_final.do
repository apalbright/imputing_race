********************************************************************************
**** Results - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 04/07/2026
Notes:
- PPP-specific counterpart to Results_final.do
- Includes Last Name, ZIP, BISG, BIFSG, and ZRP
- Uses method tags instead of fixed row positions when exporting summary CSVs
*/

capture confirm file "${ans}/PPP_zip.dta"
if _rc!=0 {
	di as error "Missing PPP ZIP results: ${ans}/PPP_zip.dta"
	exit 601
}

capture confirm file "${ans}/PPP_lastname.dta"
if _rc!=0 {
	di as error "Missing PPP last-name results: ${ans}/PPP_lastname.dta"
	exit 601
}

capture confirm file "${ans}/PPP_wru.dta"
if _rc!=0 {
	di as error "Missing PPP BISG results: ${ans}/PPP_wru.dta"
	exit 601
}

capture confirm file "${ans}/PPP_BIFSG.dta"
if _rc!=0 {
	di as error "Missing PPP BIFSG results: ${ans}/PPP_BIFSG.dta"
	exit 601
}

capture confirm file "${ans}/PPP_race_disparity.dta"
if _rc!=0 {
	di as error "Missing PPP race-disparity results: ${ans}/PPP_race_disparity.dta"
	exit 601
}

capture confirm file "${ans}/PPP_ZRP.dta"
if _rc!=0 {
	di as error "Missing PPP ZRP results: ${ans}/PPP_ZRP.dta"
	exit 601
}

capture confirm file "${ans}/PPP_Nameprism.dta"
if _rc!=0 {
	di as error "Missing PPP NamePrism results: ${ans}/PPP_Nameprism.dta"
	exit 601
}

capture confirm file "${dta}/PPP_birdie_prediction.dta"
if _rc!=0 {
	di as error "Missing PPP BIRDiE prediction file: ${dta}/PPP_birdie_prediction.dta"
	exit 601
}

capture mkdir "${ans}/Plots"

capture program drop method_label
program define method_label, rclass
	syntax, KEY(string)

	local label "`key'"
	if "`key'"=="lastname" {
		local label "Last Name"
	}
	else if "`key'"=="zip" {
		local label "ZIP"
	}
	else if "`key'"=="wru" {
		local label "BISG"
	}
	else if "`key'"=="BIFSG" {
		local label "BIFSG"
	}
	else if "`key'"=="ZRP" {
		local label "ZRP"
	}
	else if "`key'"=="Nprism" {
		local label "NamePrism"
	}
	else if "`key'"=="real" {
		local label "Real"
	}
	else if "`key'"=="birdie" {
		local label "BIRDiE"
	}

	return local label "`label'"
end

capture program drop row_value
program define row_value, rclass
	syntax varname, KEY(string)

	quietly summarize `varlist' if row_key=="`key'", meanonly
	return scalar value = r(mean)
end


tempfile zip_row lastname_row wru_row bifsg_row real_row zrp_row nprism_row

use "${ans}/PPP_zip.dta", clear
gen str12 row_key = "zip"
save `zip_row', replace

use "${ans}/PPP_lastname.dta", clear
gen str12 row_key = "lastname"
save `lastname_row', replace

use "${ans}/PPP_wru.dta", clear
gen str12 row_key = "wru"
save `wru_row', replace

use "${ans}/PPP_BIFSG.dta", clear
gen str12 row_key = "BIFSG"
save `bifsg_row', replace

use "${ans}/PPP_race_disparity.dta", clear
gen str12 row_key = "real"
save `real_row', replace

use "${ans}/PPP_ZRP.dta", clear
gen str12 row_key = "ZRP"
save `zrp_row', replace

use "${ans}/PPP_Nameprism.dta", clear
gen str12 row_key = "Nprism"
save `nprism_row', replace

use `zip_row', clear
append using `lastname_row' `wru_row' `bifsg_row' `real_row' `zrp_row' `nprism_row'
order row_key, first


****************************************************************************
** Do stats for figures
****************************************************************************

local Methods lastname zip wru BIFSG ZRP Nprism

foreach y of local Methods {

	** Real
	gen total_white_`y'= `y'_count_White_white + `y'_count_White_asian + `y'_count_White_black ///
	+ `y'_count_White_hispanic + `y'_count_White_other

	gen total_asian_`y'= `y'_count_Asian_white + `y'_count_Asian_asian + `y'_count_Asian_black ///
	+ `y'_count_Asian_hispanic + `y'_count_Asian_other

	gen total_black_`y'= `y'_count_Black_white + `y'_count_Black_asian + `y'_count_Black_black ///
	+ `y'_count_Black_hispanic + `y'_count_Black_other

	gen total_hispanic_`y'= `y'_count_Hispanic_white + `y'_count_Hispanic_asian + `y'_count_Hispanic_black ///
	+ `y'_count_Hispanic_hispanic + `y'_count_Hispanic_other

	gen total_other_`y'= `y'_count_Other_white + `y'_count_Other_asian + `y'_count_Other_black ///
	+ `y'_count_Other_hispanic + `y'_count_Other_other

	** Predicted
	gen total_white_pre_`y'= `y'_count_White_white + `y'_count_Asian_white + `y'_count_Black_white ///
	+ `y'_count_Hispanic_white + `y'_count_Other_white

	gen total_asian_pre_`y'= `y'_count_White_asian + `y'_count_Asian_asian + `y'_count_Black_asian ///
	+ `y'_count_Hispanic_asian + `y'_count_Other_asian

	gen total_black_pre_`y'= `y'_count_White_black + `y'_count_Asian_black + `y'_count_Black_black ///
	+ `y'_count_Hispanic_black + `y'_count_Other_black

	gen total_hispanic_pre_`y'= `y'_count_White_hispanic + `y'_count_Asian_hispanic + `y'_count_Black_hispanic ///
	+ `y'_count_Hispanic_hispanic + `y'_count_Other_hispanic

	gen total_other_pre_`y'= `y'_count_White_other + `y'_count_Asian_other + `y'_count_Black_other ///
	+ `y'_count_Hispanic_other + `y'_count_Other_other

}


**** Recall calculations
foreach y of local Methods {

	gen recall_white_`y'=(`y'_count_White_white/total_white_`y')*100
	gen recall_asian_`y'=(`y'_count_Asian_asian/total_asian_`y')*100
	gen recall_black_`y'=(`y'_count_Black_black/total_black_`y')*100
	gen recall_hispanic_`y'=(`y'_count_Hispanic_hispanic/total_hispanic_`y')*100
	gen recall_other_`y'=(`y'_count_Other_other/total_other_`y')*100

}


**** Precision calculations
foreach y of local Methods {

	gen precision_white_`y'=(`y'_count_White_white/total_white_pre_`y')*100
	gen precision_asian_`y'=(`y'_count_Asian_asian/total_asian_pre_`y')*100
	gen precision_black_`y'=(`y'_count_Black_black/total_black_pre_`y')*100
	gen precision_hispanic_`y'=(`y'_count_Hispanic_hispanic/total_hispanic_pre_`y')*100
	gen precision_other_`y'=(`y'_count_Other_other/total_other_pre_`y')*100

}


foreach y of local Methods {
	foreach x in white asian black hispanic other {
		replace recall_`x'_`y'=0 if recall_`x'_`y'==.
		replace precision_`x'_`y'=0 if precision_`x'_`y'==.
	}
}


**** F1 Scores
foreach y of local Methods {

	gen f1_white_`y'= (2*(precision_white_`y'/100)*(recall_white_`y'/100))/((precision_white_`y'/100)+(recall_white_`y'/100))
	gen f1_asian_`y'=(2*(precision_asian_`y'/100)*(recall_asian_`y'/100))/((precision_asian_`y'/100)+(recall_asian_`y'/100))
	gen f1_black_`y'=(2*(precision_black_`y'/100)*(recall_black_`y'/100))/((precision_black_`y'/100)+(recall_black_`y'/100))
	gen f1_hispanic_`y'=(2*(precision_hispanic_`y'/100)*(recall_hispanic_`y'/100))/((precision_hispanic_`y'/100)+(recall_hispanic_`y'/100))
	gen f1_other_`y'=(2*(precision_other_`y'/100)*(recall_other_`y'/100))/((precision_other_`y'/100)+(recall_other_`y'/100))

}

foreach y of local Methods {
	foreach x in white asian black hispanic other {
		replace f1_`x'_`y'=0 if f1_`x'_`y'==.
	}
}


** True Positives / False Negatives / False Positives
foreach y of local Methods {

	gen true_pos_`y'= (`y'_count_White_white + `y'_count_Asian_asian + `y'_count_Black_black ///
						+ `y'_count_Hispanic_hispanic + `y'_count_Other_other)

	gen false_pos_`y'= (`y'_count_Asian_white + `y'_count_Black_white + `y'_count_Hispanic_white + `y'_count_Other_white ///
						+ `y'_count_White_asian + `y'_count_Black_asian + `y'_count_Hispanic_asian + `y'_count_Other_asian ///
						+ `y'_count_Asian_black + `y'_count_White_black + `y'_count_Hispanic_black + `y'_count_Other_black ///
						+ `y'_count_Asian_hispanic + `y'_count_Black_hispanic + `y'_count_White_hispanic + `y'_count_Other_hispanic ///
						+ `y'_count_Asian_other + `y'_count_Black_other + `y'_count_White_other + `y'_count_Hispanic_other)

	gen false_neg_`y'= false_pos_`y'

}


foreach y of local Methods {

	gen micro_f1_`y'= true_pos_`y'/(true_pos_`y'+ 0.5*(false_pos_`y'+ false_neg_`y'))
	gen macro_f1_`y'= (f1_white_`y' + f1_asian_`y' + f1_black_`y' + f1_hispanic_`y' + f1_other_`y')/5

}


foreach y of local Methods {

	gen total_`y'= total_white_`y' + total_black_`y' + total_hispanic_`y' + total_asian_`y' + total_other_`y'
	gen weight_`y'_white= total_white_`y'/total_`y'
	gen weight_`y'_black= total_black_`y'/total_`y'
	gen weight_`y'_hispanic= total_hispanic_`y'/total_`y'
	gen weight_`y'_asian= total_asian_`y'/total_`y'
	gen weight_`y'_other= total_other_`y'/total_`y'

	gen weighted_f1_`y'=f1_white_`y'*weight_`y'_white + f1_black_`y'*weight_`y'_black + f1_hispanic_`y'*weight_`y'_hispanic ///
						+ f1_asian_`y'*weight_`y'_asian + f1_other_`y'*weight_`y'_other

}


****** Missing Observations
egen total_observations_max=max(total_observations)

foreach y of local Methods {

	gen missing_`y'= 100 - (total_`y'/total_observations_max)*100
	replace missing_`y'=0 if missing_`y'<=0

}


********** Race Disparity
foreach y of local Methods {

	gen gap_black_white_`y'= (`y'_fintech_black/`y'_black)*100 - (`y'_fintech_white/`y'_white)*100
	gen gap_black_hispanic_`y'= (`y'_fintech_black/`y'_black)*100 - (`y'_fintech_hispanic/`y'_hispanic)*100
	gen gap_black_asian_`y'= (`y'_fintech_black/`y'_black)*100 - (`y'_fintech_asian/`y'_asian)*100
	gen gap_hispanic_white_`y'= (`y'_fintech_hispanic/`y'_hispanic)*100 - (`y'_fintech_white/`y'_white)*100
	gen gap_hispanic_asian_`y'= (`y'_fintech_hispanic/`y'_hispanic)*100 - (`y'_fintech_asian/`y'_asian)*100
	gen gap_asian_white_`y'= (`y'_fintech_asian/`y'_asian)*100 - (`y'_fintech_white/`y'_white)*100

}


gen gap_black_white_real= (total_fintech_black/total_black)*100 - (total_fintech_white/total_white)*100
gen gap_black_hispanic_real= (total_fintech_black/total_black)*100 - (total_fintech_hispanic/total_hispanic)*100
gen gap_black_asian_real= (total_fintech_black/total_black)*100 - (total_fintech_asian/total_asian)*100
gen gap_hispanic_white_real= (total_fintech_hispanic/total_hispanic)*100 - (total_fintech_white/total_white)*100
gen gap_hispanic_asian_real= (total_fintech_hispanic/total_hispanic)*100 - (total_fintech_asian/total_asian)*100
gen gap_asian_white_real= (total_fintech_asian/total_asian)*100 - (total_fintech_white/total_white)*100

foreach y of local Methods {

	gen gap_black_`y'= (`y'_fintech_black/`y'_black)*100
	gen gap_hispanic_`y'= (`y'_fintech_hispanic/`y'_hispanic)*100
	gen gap_asian_`y'= (`y'_fintech_asian/`y'_asian)*100
	gen gap_white_`y'= (`y'_fintech_white/`y'_white)*100

}

gen gap_black_real= (total_fintech_black/total_black)*100
gen gap_hispanic_real= (total_fintech_hispanic/total_hispanic)*100
gen gap_asian_real= (total_fintech_asian/total_asian)*100
gen gap_white_real= (total_fintech_white/total_white)*100


**** Population
foreach y of local Methods {

	gen white_pop_`y'= (total_white_pre_`y'/total_`y')*100
	gen asian_pop_`y'= (total_asian_pre_`y'/total_`y')*100
	gen black_pop_`y'= (total_black_pre_`y'/total_`y')*100
	gen hispanic_pop_`y'= (total_hispanic_pre_`y'/total_`y')*100
	gen other_pop_`y'= (total_other_pre_`y'/total_`y')*100

}

gen white_pop_real= (total_white/total_observations_max)*100
gen asian_pop_real= (total_asian/total_observations_max)*100
gen black_pop_real= (total_black/total_observations_max)*100
gen hispanic_pop_real= (total_hispanic/total_observations_max)*100
gen other_pop_real= (total_other/total_observations_max)*100


preserve
use "${dta}/PPP_birdie_prediction.dta", clear
foreach gap in black_white black_hispanic black_asian hispanic_white hispanic_asian asian_white {
	quietly summarize estimate if gap_name=="`gap'", meanonly
	scalar gap_`gap'_birdie = r(mean)*100
}
restore


*************************************************************************
**** Export to CSV
*************************************************************************


*** Missing Rates
preserve

tempname missing_post
tempfile missing_csv
postfile `missing_post' str12 Method double Missing using `missing_csv', replace

foreach key of local Methods {
	quietly method_label, key("`key'")
	local label "`r(label)'"
	quietly row_value missing_`key', key("`key'")
	post `missing_post' ("`label'") (r(value))
}

postclose `missing_post'
use `missing_csv', clear
export delimited using "${ans}/Plots/PPP_01_missing.csv", replace

restore


*** Recall Rate
preserve

tempname recall_post
tempfile recall_csv
postfile `recall_post' str12 Method double White Black Hispanic Asian Other using `recall_csv', replace

foreach key of local Methods {
	quietly method_label, key("`key'")
	local label "`r(label)'"
	quietly row_value recall_white_`key', key("`key'")
	local white = r(value)
	quietly row_value recall_black_`key', key("`key'")
	local black = r(value)
	quietly row_value recall_hispanic_`key', key("`key'")
	local hispanic = r(value)
	quietly row_value recall_asian_`key', key("`key'")
	local asian = r(value)
	quietly row_value recall_other_`key', key("`key'")
	local other = r(value)
	post `recall_post' ("`label'") (`white') (`black') (`hispanic') (`asian') (`other')
}

postclose `recall_post'
use `recall_csv', clear
export delimited using "${ans}/Plots/PPP_02_recall.csv", replace

restore


*** Precision Rate
preserve

tempname precision_post
tempfile precision_csv
postfile `precision_post' str12 Method double White Black Hispanic Asian Other using `precision_csv', replace

foreach key of local Methods {
	quietly method_label, key("`key'")
	local label "`r(label)'"
	quietly row_value precision_white_`key', key("`key'")
	local white = r(value)
	quietly row_value precision_black_`key', key("`key'")
	local black = r(value)
	quietly row_value precision_hispanic_`key', key("`key'")
	local hispanic = r(value)
	quietly row_value precision_asian_`key', key("`key'")
	local asian = r(value)
	quietly row_value precision_other_`key', key("`key'")
	local other = r(value)
	post `precision_post' ("`label'") (`white') (`black') (`hispanic') (`asian') (`other')
}

postclose `precision_post'
use `precision_csv', clear
export delimited using "${ans}/Plots/PPP_03_precision.csv", replace

restore


*** F1 by Race
preserve

tempname f1race_post
tempfile f1race_csv
postfile `f1race_post' str12 Method double White Black Hispanic Asian Other using `f1race_csv', replace

foreach key of local Methods {
	quietly method_label, key("`key'")
	local label "`r(label)'"
	quietly row_value f1_white_`key', key("`key'")
	local white = r(value)*100
	quietly row_value f1_black_`key', key("`key'")
	local black = r(value)*100
	quietly row_value f1_hispanic_`key', key("`key'")
	local hispanic = r(value)*100
	quietly row_value f1_asian_`key', key("`key'")
	local asian = r(value)*100
	quietly row_value f1_other_`key', key("`key'")
	local other = r(value)*100
	post `f1race_post' ("`label'") (`white') (`black') (`hispanic') (`asian') (`other')
}

postclose `f1race_post'
use `f1race_csv', clear
export delimited using "${ans}/Plots/PPP_04_F1_race.csv", replace

restore


*** Aggregated F1
preserve

tempname f1agg_post
tempfile f1agg_csv
postfile `f1agg_post' str12 Method double Weighted Micro Macro using `f1agg_csv', replace

foreach key of local Methods {
	quietly method_label, key("`key'")
	local label "`r(label)'"
	quietly row_value weighted_f1_`key', key("`key'")
	local weighted = r(value)*100
	quietly row_value micro_f1_`key', key("`key'")
	local micro = r(value)*100
	quietly row_value macro_f1_`key', key("`key'")
	local macro = r(value)*100
	post `f1agg_post' ("`label'") (`weighted') (`micro') (`macro')
}

postclose `f1agg_post'
use `f1agg_csv', clear
export delimited using "${ans}/Plots/PPP_05_F1_aggregated.csv", replace

restore


*** Population
preserve

tempname pop_post
tempfile pop_csv
postfile `pop_post' str12 Method double White Black Hispanic Asian Other Distance using `pop_csv', replace

quietly row_value white_pop_real, key("real")
	local white_real = r(value)
quietly row_value black_pop_real, key("real")
	local black_real = r(value)
quietly row_value hispanic_pop_real, key("real")
	local hispanic_real = r(value)
quietly row_value asian_pop_real, key("real")
	local asian_real = r(value)
quietly row_value other_pop_real, key("real")
	local other_real = r(value)

foreach key of local Methods {
	quietly method_label, key("`key'")
	local label "`r(label)'"
	quietly row_value white_pop_`key', key("`key'")
	local white = r(value)
	quietly row_value black_pop_`key', key("`key'")
	local black = r(value)
	quietly row_value hispanic_pop_`key', key("`key'")
	local hispanic = r(value)
	quietly row_value asian_pop_`key', key("`key'")
	local asian = r(value)
	quietly row_value other_pop_`key', key("`key'")
	local other = r(value)
	local distance = sqrt((`white'-`white_real')^2 + (`black'-`black_real')^2 + (`hispanic'-`hispanic_real')^2 + (`asian'-`asian_real')^2 + (`other'-`other_real')^2)
	post `pop_post' ("`label'") (`white') (`black') (`hispanic') (`asian') (`other') (`distance')
}

post `pop_post' ("Real") (`white_real') (`black_real') (`hispanic_real') (`asian_real') (`other_real') (.)

postclose `pop_post'
use `pop_csv', clear
export delimited using "${ans}/Plots/PPP_08_population.csv", replace

restore


*** Race Disparity
preserve

tempname gap_post
tempfile gap_csv
postfile `gap_post' str12 Method double Black_White Black_Hispanic Black_Asian Hispanic_White Hispanic_Asian Asian_White using `gap_csv', replace

foreach key of local Methods {
	quietly method_label, key("`key'")
	local label "`r(label)'"
	quietly row_value gap_black_white_`key', key("`key'")
	local bw = r(value)
	quietly row_value gap_black_hispanic_`key', key("`key'")
	local bh = r(value)
	quietly row_value gap_black_asian_`key', key("`key'")
	local ba = r(value)
	quietly row_value gap_hispanic_white_`key', key("`key'")
	local hw = r(value)
	quietly row_value gap_hispanic_asian_`key', key("`key'")
	local ha = r(value)
	quietly row_value gap_asian_white_`key', key("`key'")
	local aw = r(value)
	post `gap_post' ("`label'") (`bw') (`bh') (`ba') (`hw') (`ha') (`aw')
}

post `gap_post' ("BIRDiE") (gap_black_white_birdie) (gap_black_hispanic_birdie) (gap_black_asian_birdie) ///
	(gap_hispanic_white_birdie) (gap_hispanic_asian_birdie) (gap_asian_white_birdie)

quietly row_value gap_black_white_real, key("real")
local bw_real = r(value)
quietly row_value gap_black_hispanic_real, key("real")
local bh_real = r(value)
quietly row_value gap_black_asian_real, key("real")
local ba_real = r(value)
quietly row_value gap_hispanic_white_real, key("real")
local hw_real = r(value)
quietly row_value gap_hispanic_asian_real, key("real")
local ha_real = r(value)
quietly row_value gap_asian_white_real, key("real")
local aw_real = r(value)

post `gap_post' ("Real") (`bw_real') (`bh_real') (`ba_real') (`hw_real') (`ha_real') (`aw_real')

postclose `gap_post'
use `gap_csv', clear
export delimited using "${ans}/Plots/PPP_07_all_gaps.csv", replace

restore


*** Race Disparity - Raw Numbers
preserve

tempname rates_post
tempfile rates_csv
postfile `rates_post' str12 Method double Black Hispanic Asian White using `rates_csv', replace

foreach key of local Methods {
	quietly method_label, key("`key'")
	local label "`r(label)'"
	quietly row_value gap_black_`key', key("`key'")
	local black = r(value)
	quietly row_value gap_hispanic_`key', key("`key'")
	local hispanic = r(value)
	quietly row_value gap_asian_`key', key("`key'")
	local asian = r(value)
	quietly row_value gap_white_`key', key("`key'")
	local white = r(value)
	post `rates_post' ("`label'") (`black') (`hispanic') (`asian') (`white')
}

quietly row_value gap_black_real, key("real")
local black_real = r(value)
quietly row_value gap_hispanic_real, key("real")
local hispanic_real = r(value)
quietly row_value gap_asian_real, key("real")
local asian_real = r(value)
quietly row_value gap_white_real, key("real")
local white_real_rate = r(value)

post `rates_post' ("Real") (`black_real') (`hispanic_real') (`asian_real') (`white_real_rate')

postclose `rates_post'
use `rates_csv', clear
export delimited using "${ans}/Plots/PPP_06_fintech_rates.csv", replace

restore
