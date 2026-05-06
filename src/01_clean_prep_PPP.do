*******************************************************************************
*** Main - PPP
********************************************************************************


clear all
set more off

/*
Created by: Weiran
Date: 03/26/2026
Notes:
- Stata prep step after src/00_clean_raw_PPP.py
- Builds PPP_clean.dta aligned to the NC voter-style schema
- Keeps Hispanic in ethnic_code / Race_Ethnicity_Simple rather than encoding it as race_code
*/


* Run from the project root or from src/.
capture confirm file "src/01_clean_prep_PPP.do"
if _rc!=0 {
	capture confirm file "01_clean_prep_PPP.do"
	if _rc==0 {
		cd ".."
	}
	else {
		di as error "Run this script from the project root or src/."
		exit 601
	}
}


global data "./Data"
global raw_ppp "./Data/raw/PPP"
global support "./Data/raw/geo"
global processed "./Data/interim/processed_PPP"
global method_inputs "./Data/interim/method_inputs"
global predictions "./Data/interim/predictions"
global ans "./Results"
global codes "./src"

capture mkdir "${processed}"
capture mkdir "./Data/interim"
capture mkdir "${method_inputs}"
capture mkdir "${predictions}"


********************************************************************************
**** Cleaning PPP parsed file
********************************************************************************


local inputfile "${processed}/PPP_person_names_final.csv"
capture confirm file "`inputfile'"
if _rc!=0 {
	di as error "Missing final PPP person-name input: `inputfile'"
	di as error "Run python src/00_clean_raw_PPP.py before this Stata prep step."
	exit 601
}


import delimited "`inputfile'", clear varnames(1) stringcols(_all) case(preserve)


foreach var in first_name middle_name last_name BorrowerState BorrowerZip BorrowerAddress BorrowerCity Gender Race Ethnicity fintech {
	capture confirm variable `var'
	if _rc!=0 {
		di as error "Missing required column: `var'"
		exit 111
	}
}


foreach var in first_name middle_name last_name BorrowerState BorrowerZip BorrowerAddress BorrowerCity Gender Race Ethnicity ///
Race_Ethnicity_Simple parse_flag BorrowerName {
	capture confirm variable `var'
	if _rc==0 {
		replace `var' = trim(`var')
		replace `var' = "" if inlist(upper(`var'), "NAN", "NONE", "<NA>")
	}
}


capture destring fintech, replace force
count if missing(fintech)
if r(N)>0 {
	di as error "fintech has missing or non-numeric values"
	exit 459
}

count if fintech!=0 & fintech!=1
if r(N)>0 {
	di as error "fintech contains values outside 0/1"
	exit 459
}


gen state = upper(trim(BorrowerState))
replace state = substr(state, 1, 2)

gen zip_code = ""
replace zip_code = regexs(1) if regexm(BorrowerZip, "([0-9][0-9][0-9][0-9][0-9])")

gen street_address = upper(trim(BorrowerAddress))
replace street_address = "" if inlist(street_address, "NAN", "NONE", "<NA>")

gen house_number = ""
replace house_number = upper(regexs(1)) if regexm(BorrowerAddress, "^[ ]*([0-9]+[A-Za-z]?)")

gen city = upper(trim(BorrowerCity))
replace city = "" if inlist(city, "NAN", "NONE", "<NA>")


replace first_name = upper(trim(first_name))
replace middle_name = upper(trim(middle_name))
replace last_name = upper(trim(last_name))


gen gender_code = "U"
replace gender_code = "M" if upper(trim(Gender))=="MALE OWNED"
replace gender_code = "F" if upper(trim(Gender))=="FEMALE OWNED"


gen ethnic_code = "UN"
replace ethnic_code = "HL" if upper(trim(Ethnicity))=="HISPANIC OR LATINO"
replace ethnic_code = "NL" if upper(trim(Ethnicity))=="NOT HISPANIC OR LATINO"


gen race_code = "U"
replace race_code = "W" if upper(trim(Race))=="WHITE"
replace race_code = "B" if upper(trim(Race))=="BLACK OR AFRICAN AMERICAN"
replace race_code = "A" if upper(trim(Race))=="ASIAN"
replace race_code = "I" if upper(trim(Race))=="AMERICAN INDIAN OR ALASKA NATIVE"
replace race_code = "M" if upper(trim(Race))=="TWO OR MORE RACES"
replace race_code = "P" if upper(trim(Race))=="NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER"
replace race_code = "O" if upper(trim(Race))=="OTHER"
* NC voter files do not use a Hispanic race code. When PPP provides only a Hispanic ethnicity label
* without a separate race, keep race_code as unknown and rely on ethnic_code / Race_Ethnicity_Simple.
replace race_code = "U" if upper(trim(Race))=="HISPANIC OR LATINO"


foreach var in Race Ethnicity Race_Ethnicity_Simple parse_flag BorrowerName {
	capture confirm variable `var'
	if _rc==0 {
		replace `var' = upper(trim(`var'))
		replace `var' = "" if inlist(`var', "NAN", "NONE", "<NA>")
	}
}


local keepvars first_name middle_name last_name state zip_code street_address house_number city fintech gender_code ethnic_code race_code
local lastvar race_code

order `keepvars'

foreach var in Race Ethnicity Race_Ethnicity_Simple parse_flag BorrowerName {
	capture confirm variable `var'
	if _rc==0 {
		order `var', after(`lastvar')
		local lastvar `var'
		local keepvars `keepvars' `var'
	}
}


keep `keepvars'

compress

save "${processed}/PPP_clean.dta", replace


///////////////////////////////////////////
/// Run PPP method prep files
//////////////////////////////////////////


*** Run do files for different methods
do "${codes}/sub/PPP_last_name_clean.do"
do "${codes}/sub/PPP_WRU_clean.do"
do "${codes}/sub/PPP_BIFSG_clean.do"
do "${codes}/sub/PPP_ZRP_clean.do"
do "${codes}/sub/PPP_NamePrism_clean.do"
do "${codes}/sub/PPP_birdie_clean.do"
