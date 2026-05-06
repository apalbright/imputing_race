*******************************************************************************
*** Main - PPP
********************************************************************************


clear all
set more off

/*
Created by: Weiran
Date: 03/26/2026
Notes:
- PPP-specific counterpart to 04_merge_all_methods.do
- Matches the NC structure; ZRP is wired through PPP_Results_final.do
- Named to mirror the NC main file with a _PPP suffix
*/

* Run from the project root or from src/.
capture confirm file "src/05_merge_all_methods_PPP.do"
if _rc!=0 {
	capture confirm file "05_merge_all_methods_PPP.do"
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


*** Run do files for different methods
do "${codes}/sub/PPP_last_name_merge.do"
do "${codes}/sub/PPP_WRU_merge.do"
do "${codes}/sub/PPP_BIFSG_merge.do"
do "${codes}/sub/PPP_ZRP_merge.do"
do "${codes}/sub/PPP_NamePrism_merge.do"
do "${codes}/sub/PPP_zip.do"
do "${codes}/sub/PPP_Race_disparity.do"


*** Run Results do file
do "${codes}/sub/PPP_Results_final.do"
