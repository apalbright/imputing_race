********************************************************************************
**** BIFSG Method - PPP
********************************************************************************

clear all
set more off

/*
Created by: Weiran
Date: 04/07/2026
Notes:
- PPP-specific counterpart to the staged BIFSG NC scripts
- Builds a nationwide ZIP-to-tract lookup from HUD USPS crosswalk data
- Preserves PPP row count and assigns a stable bifsg_id for 1:1 merge-back
*/

local crosswalk_dta "${support}/ZIP_TRACT_122025_bestres.dta"
local crosswalk_xlsx "${support}/ZIP_TRACT_122025.xlsx"


capture confirm file "`crosswalk_dta'"
if _rc!=0 {
	capture confirm file "`crosswalk_xlsx'"
	if _rc!=0 {
		di as error "Missing ZIP-to-tract workbook: `crosswalk_xlsx'"
		exit 601
	}

	import excel "`crosswalk_xlsx'", sheet("Export Worksheet") firstrow allstring clear

	keep ZIP TRACT USPS_ZIP_PREF_STATE RES_RATIO

	rename ZIP zip_code
	rename TRACT tract11
	rename USPS_ZIP_PREF_STATE preferred_state

	replace zip_code = trim(zip_code)
	replace tract11 = trim(tract11)
	replace preferred_state = upper(trim(preferred_state))

	replace zip_code = substr("00000" + zip_code, -5, 5) if zip_code!=""
	replace tract11 = substr("00000000000" + tract11, -11, 11) if tract11!=""

	destring RES_RATIO, replace force

	drop if zip_code==""
	drop if tract11==""
	drop if preferred_state==""

	sort zip_code RES_RATIO
	by zip_code: keep if _n==_N

	keep zip_code tract11 preferred_state
	compress
	save "`crosswalk_dta'", replace
}


use "${processed}/PPP_clean.dta", clear

gen long bifsg_id = _n

capture confirm string variable zip_code
if _rc!=0 {
	tostring zip_code, replace force
}
replace zip_code = trim(zip_code)
replace zip_code = substr("00000" + zip_code, -5, 5) if zip_code!=""

capture confirm string variable state
if _rc!=0 {
	tostring state, replace force
}
rename state borrower_state
replace borrower_state = upper(trim(borrower_state))

	gen firstname = upper(trim(first_name))
	gen surname = upper(trim(last_name))

	merge m:1 zip_code using "`crosswalk_dta'", nogen keep(master match)

	gen state = preferred_state
	gen byte state_mismatch = borrower_state!="" & preferred_state!="" & borrower_state!=preferred_state
	gen county = substr(tract11, 3, 3) if tract11!=""
	gen tract = substr(tract11, 6, 6) if tract11!=""

	order bifsg_id zip_code borrower_state preferred_state state state_mismatch county tract firstname surname fintech race_code ethnic_code
	keep bifsg_id firstname surname state county tract zip_code borrower_state preferred_state state_mismatch fintech race_code ethnic_code

	compress
	save "${method_inputs}/PPP_BIFSG_interim.dta", replace
