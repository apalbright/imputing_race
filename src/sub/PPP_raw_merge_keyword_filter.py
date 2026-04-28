"""Merge raw PPP files and filter to person-name borrower records."""

from pathlib import Path
import os
import re

import numpy as np
import pandas as pd


def _find_project_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "Data").is_dir() and (path / "src").is_dir():
            return path
    raise FileNotFoundError("Could not find project root containing Data/ and src/.")


def main(project_root: Path) -> None:
    project_root = Path(project_root).resolve()
    raw_data_path = project_root / "Data" / "raw" / "PPP"
    intermediate_data_path = project_root / "Data" / "intermediate"
    intermediate_data_path.mkdir(parents=True, exist_ok=True)

    if not raw_data_path.is_dir():
        raise FileNotFoundError(f"Missing raw PPP input directory: {raw_data_path}")

    print(f"Project root: {project_root}")
    print(f"Raw PPP input directory: {raw_data_path}")

    # Load all 12 files + 150k+ file (same as R script)
    files = [f"public_up_to_150k_{i}_240930.csv" for i in range(1, 13)]
    files.append("public_150k_plus_240930.csv")

    missing_files = [file for file in files if not (raw_data_path / file).is_file()]
    if missing_files:
        raise FileNotFoundError(
            "Missing raw PPP files in "
            f"{raw_data_path}: {', '.join(missing_files)}"
        )

    print(f"Loading {len(files)} files...")

    # Load and concatenate all files
    dfs = []
    for i, file in enumerate(files, 1):
        file_path = os.path.join(raw_data_path, file)
        try:
            df = pd.read_csv(file_path, low_memory=False, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, low_memory=False, encoding='latin-1')
        df['file_id'] = i
        dfs.append(df)
        print(f"  Loaded {file}: {len(df):,} rows")

    # Combine all dataframes
    ppp_raw = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal raw records: {len(ppp_raw):,}")

    # Filter to keep only first draw loans (PPP), exclude second draw (PPS)
    before_first_draw = len(ppp_raw)

    print("=" * 60)
    print("ProcessingMethod distribution:")
    print("-" * 40)
    print(ppp_raw['ProcessingMethod'].value_counts(dropna=False))

    ppp_first_draw = ppp_raw[ppp_raw['ProcessingMethod'] == 'PPP'].copy()
    after_first_draw = len(ppp_first_draw)

    print(f"\n{'=' * 60}")
    print("FIRST DRAW FILTER RESULTS")
    print("=" * 60)
    print(f"Before filter:             {before_first_draw:>12,}")
    print(f"First draw (PPP) kept:     {after_first_draw:>12,}")
    print(f"Second draw (PPS) removed: {before_first_draw - after_first_draw:>12,}")
    print(f"Removal rate:              {(before_first_draw - after_first_draw) / before_first_draw * 100:>11.2f}%")

    # Date cutoff: February 24, 2021
    cutoff_date = pd.to_datetime("02/24/2021", format="%m/%d/%Y")

    # Convert DateApproved to datetime
    ppp_first_draw['DateApproved'] = pd.to_datetime(
        ppp_first_draw['DateApproved'], format="%m/%d/%Y", errors='coerce'
    )

    before_date_filter = len(ppp_first_draw)
    ppp_date_filtered = ppp_first_draw[ppp_first_draw['DateApproved'] < cutoff_date].copy()
    after_date_filter = len(ppp_date_filtered)

    print("=" * 60)
    print("DATE FILTER RESULTS")
    print("=" * 60)
    print(f"Date cutoff: {cutoff_date.strftime('%B %d, %Y')}")
    print(f"Before date filter:  {before_date_filter:>12,}")
    print(f"After date filter:   {after_date_filter:>12,}")
    print(f"Removed:             {before_date_filter - after_date_filter:>12,} ({(before_date_filter - after_date_filter) / before_date_filter * 100:.2f}%)")
    print(f"\nDate range in filtered data:")
    print(f"  Earliest: {ppp_date_filtered['DateApproved'].min()}")
    print(f"  Latest:   {ppp_date_filtered['DateApproved'].max()}")

    # Filter by Race (not NA and not "Unanswered")
    before_race = len(ppp_date_filtered)

    ppp_race_clean = ppp_date_filtered[
        (ppp_date_filtered['Race'].notna()) & 
        (ppp_date_filtered['Race'] != 'Unanswered')
    ].copy()
    after_race = len(ppp_race_clean)

    print("=" * 60)
    print("RACE FILTER RESULTS")
    print("=" * 60)
    print(f"Before race filter:  {before_race:>12,}")
    print(f"After race filter:   {after_race:>12,}")
    print(f"Removed:             {before_race - after_race:>12,} ({(before_race - after_race) / before_race * 100:.2f}%)")

    # Filter by valid BorrowerZip
    before_zip = len(ppp_race_clean)

    ppp_zip_clean = ppp_race_clean[
        (ppp_race_clean['BorrowerZip'].notna()) &
        (ppp_race_clean['BorrowerZip'].astype(str).str.strip() != '') &
        (ppp_race_clean['BorrowerZip'].astype(str).str.upper() != 'NAN')
    ].copy()
    after_zip = len(ppp_zip_clean)

    print("=" * 60)
    print("ZIP FILTER RESULTS")
    print("=" * 60)
    print(f"Before zip filter:   {before_zip:>12,}")
    print(f"After zip filter:    {after_zip:>12,}")
    print(f"Removed:             {before_zip - after_zip:>12,} ({(before_zip - after_zip) / before_zip * 100:.2f}%)")

    def has_special_or_number(name: str) -> bool:
        """Check if name contains special characters or numbers"""
        if pd.isna(name):
            return False
        return bool(re.search(r"[0-9&/@#]", str(name)))

    before_special = len(ppp_zip_clean)
    ppp_zip_clean['flag_special_or_number'] = ppp_zip_clean['BorrowerName'].apply(has_special_or_number)

    ppp_zip_clean = ppp_zip_clean[~ppp_zip_clean['flag_special_or_number']].copy()
    after_special = len(ppp_zip_clean)

    print("=" * 60)
    print("SPECIAL CHARACTER FILTER RESULTS")
    print("=" * 60)
    print(f"Before filter:       {before_special:>12,}")
    print(f"After filter:        {after_special:>12,}")
    print(f"Removed:             {before_special - after_special:>12,} ({(before_special - after_special) / before_special * 100:.2f}%)")

    # ── 6b. Remove NaN / NULL BorrowerNames ────────────────────────────
    before_null = len(ppp_zip_clean)

    null_mask = (
        ppp_zip_clean['BorrowerName'].isna() |
        ppp_zip_clean['BorrowerName'].astype(str).str.strip().isin(['', 'NULL', 'NULL NULL'])
    )
    ppp_zip_clean = ppp_zip_clean[~null_mask].copy()
    after_null = len(ppp_zip_clean)

    print("=" * 60)
    print("NULL / MISSING NAME FILTER RESULTS")
    print("=" * 60)
    print(f"Before filter:       {before_null:>12,}")
    print(f"After filter:        {after_null:>12,}")
    print(f"Removed:             {before_null - after_null:>12,}")

    # ── Tier 1: Legal/business suffix tokens ──────────────────────────
    # A SINGLE match → classified as business
    LEGAL_SUFFIXES = {
        "LLC", "L.L.C", "INC", "INCORPORATED", "CORP", "CORPORATION",
        "LTD", "LIMITED", "PLLC", "P.L.L.C", "PC", "P.C", "PA", "P.A",
        "LP", "L.P", "LLP", "L.L.P", "PLC",
    }

    # ── Tier 2: Broad business keywords ──────────────────────────────
    # A SINGLE match → classified as business
    # NOTE: Tier 1 suffixes and DBA are intentionally excluded here —
    #       they are already caught in earlier tiers.
    BUSINESS_KEYWORDS_BROAD = {
        # Entity types (non-suffix)
        "COMPANY", "CO",
        "ENTERPRISES", "ENTERPRISE",
        "PS","COMPANIES",
        # Financial institutions
        "BANK", "BANC", "CREDIT", "UNION",
        # Corporate / Organizational
        "SERVICES", "SERVICE", "GROUP", "HOLDINGS", "CONSULTING", "CONSULTANTS",
        "SOLUTIONS", "PARTNERS", "PARTNERSHIP", "ASSOCIATES", "ASSOCIATION",
        "FOUNDATION", "INSTITUTE", "CENTER",
        "MANAGEMENT", "MGMT",
        # Healthcare
        "CLINIC", "HOSPITAL", "MEDICAL", "DENTAL", "HEALTH", "CARE",
        "CHIROPRACTIC", "DENTISTRY",
        # Food / Hospitality
        "RESTAURANT", "CAFE", "BAR", "GRILL", "PIZZA", "FOOD",
        "KITCHEN", "DELI", "BAKERY", "CATERING",
        "INN", "LODGE", "LOUNGE", "MOTEL",
        # Personal Services
        "SALON", "SPA", "BEAUTY", "BARBER", "NAIL", "HAIR",
        "TAILOR", "TAILORING", "MASSAGE",
        # Construction / Trades
        "CONSTRUCTION", "BUILDERS", "BUILDING", "ROOFING", "PLUMBING", "ELECTRIC",
        "CONTRACTING", "PAINTING", "SIDING", "RESOURCE", "RESOURCES",
        "HVAC",
        # Auto / Transport
        "AUTO", "AUTOMOTIVE", "MOTORS", "TRUCKING", "TRANSPORT", "LOGISTICS",
        "TOWING", "TOURS", "CHARTERS",
        # Retail
        "SHOP", "STORE", "MART", "MARKET", "MKT", "SUPPLY", "SUPPLIES",
        "DEPOT", "WAREHOUSE", "DISTRIBUTION",
        "FABRIC", "CERAMIC",
        # Real Estate / Finance
        "REALTY", "REAL ESTATE", "PROPERTIES", "PROPERTY", "INVESTMENTS",
        "AGENCY", "INSURANCE", "FINANCIAL", "ACCOUNTING",
        "TAX", "BOOKKEEPING",
        # Tech
        "TECHNOLOGIES", "TECHNOLOGY", "TECH", "SYSTEMS",
        # Maintenance / Installation
        "CLEANING", "MAINTENANCE", "REPAIR", "INSTALLATION",
        # Education
        "SCHOOL", "ACADEMY", "LEARNING", "EDUCATION", "TRAINING",
        "UNIVERSITY", "COLLEGE",
        # Government / Public sector
        "CITY", "COUNTY", "STATE", "TOWNSHIP", "DEPARTMENT",
        # Religious
        "CHURCH", "MINISTRIES", "MINISTRY",
        "PARISH", "ABBEY",
        # Landscaping / Agriculture
        "LANDSCAPING", "LAWN", "GARDEN", "TREE", "TREES", "BUSHES", "SHRUBS",
        "FARM", "FARMS", "RANCH", "DAIRY", "CATTLE",
        "FISHING", 
        # Creative / Media
        "PHOTOGRAPHY", "STUDIO", "DESIGN", "CREATIVE", "MEDIA", "PRODUCTION",
        "IMAGE", "IMAGING",
        # Entertainment / Arts
        "ENTERTAINMENT", "ORCHESTRA", "BREWERY",
        # Rentals
        "RENTALS", "RENTAL", "LEASING",
        # Legal
        "THE", "OFFICE", "OFFICES", "LAW", "LEGAL", "ATTORNEY",
        "TRUST", "ESTATE",
        # Fitness
        "FITNESS", "GYM", "YOGA", "WELLNESS",
        # Misc services
        "INTERNATIONAL", "NATIONAL", "GLOBAL", "WORLDWIDE",
        "PROFESSIONAL", "PROFESSIONALS",
        "DETAIL", "DETAILING", "CARWASH", "WASH",
        "TAXIDERMY", "GROOMING", "PET", "VETERINARY", "VET",
        "MACHINE",
        # Childcare
        "DAYCARE",
        # Organizations
        "CHAMBER", "COMMERCE", "ASSEMBLY",
        # Pattern: "X OF Y" → business
        "OF","BY",
        # Added from 4 part names
        "THERAPY","CLUB","REALTOR","PHYSICAL","CUSTOM","CLEANERS","APLC","CONTRACTOR",
        "CHILDCARE","PRODUCTS","SOCIETY","PRODUCTIONS","MDPA","MDPC","APMC","CUISINE",
        "DEVELOPMENT","PRESCHOOL","ARCHITECT","ARCHITECTS","FUNERAL","BOUTIQUE",
        "CONTROL","PEST","WORKS","HOMES","METAL","TRAVEL","ASSISTED","EXPRESS",
        "ELECTRICAL","MARKETING","SPORTS","COUNCIL","FOODS","PUBLIC","BUSINESS",
        "SURGERY","NETWORK","CHARTERED","SCREEN","TRANSPORTATION","BROKER","STORAGE",
        "PRACTICE","DESIGNS","ALLIANCE","FARMING","HARDWOOD","MARTIAL","PRINTING",
        "IMPROVEMENT","CARPENTRY","COURSE","DINER","SHOPPE","CREATIONS","PROGRAM",
        "AUTHORITY",
        "PHYSICAL THERAPY","ASSISTED LIVING","FUNERAL HOME","PEST CONTROL",
        "COUNTRY CLUB","GOLF CLUB","GOLF COURSE","FAMILY MEDICINE","FAMILY PRACTICE",
        "FAMILY CHILDCARE","SCREEN PRINTING","HOME IMPROVEMENT",
        "ELECTRICAL CONTRACTOR","GENERAL CONTRACTOR","PLASTIC SURGERY",
        "INTERNAL MEDICINE","MARTIAL ARTS","PRESSURE WASHING","SHEET METAL",
        "ICE CREAM","FINE ART"

    }

    print(f"Tier 1 – Legal suffixes (1 match = business):   {len(LEGAL_SUFFIXES)} keywords")
    print(f"Tier 2 – Broad keywords (1 match = business):   {len(BUSINESS_KEYWORDS_BROAD)} keywords")
    print(f"Tier 3 – Contains 'DBA'")

    def _find_whole_word_matches(name_upper, keywords):
        """Return set of keywords that appear as whole words in name_upper."""
        matched = set()
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, name_upper):
                matched.add(kw)
        return matched


    def is_business_name(name):
        """
        Multi-tier check whether a borrower name is a business.
        Returns (True/False, reason_string, matched_keywords_list).

        Tier 1: Contains any legal suffix → business
        Tier 2: Contains any broad business keyword → business
        Tier 3: Contains "DBA" (Doing Business As) → business
        """
        if pd.isna(name):
            return False, "NA", []

        name_upper = str(name).upper().strip()

        # Tier 1 – Legal suffixes (single match)
        tier1 = _find_whole_word_matches(name_upper, LEGAL_SUFFIXES)
        if tier1:
            return True, "Tier1_legal_suffix", list(tier1)

        # Tier 3 – DBA (check before Tier 2 since it's a strong signal)
        if re.search(r'\bDBA\b', name_upper):
            return True, "Tier3_DBA", ["DBA"]

        # Tier 2 – Broad keywords (1+ match)
        tier2 = _find_whole_word_matches(name_upper, BUSINESS_KEYWORDS_BROAD)
        if len(tier2) >= 1:
            return True, "Tier2_keyword", list(tier2)

        return False, "person", list(tier2)


    def get_matched_keywords(name):
        """Return all matched keywords across all tiers for analysis."""
        if pd.isna(name):
            return []
        name_upper = str(name).upper().strip()
        all_matched = set()
        all_matched |= _find_whole_word_matches(name_upper, LEGAL_SUFFIXES)
        all_matched |= _find_whole_word_matches(name_upper, BUSINESS_KEYWORDS_BROAD)
        if re.search(r'\bDBA\b', name_upper):
            all_matched.add("DBA")
        return sorted(all_matched)


    # ── Test the multi-tier filter ──
    test_names = [
        "JOHN SMITH",
        "MOUNTAIN VIEW TRUCKING LLC",
        "DAVID J BERGMAN",
        "FIRST NATIONAL BANK",
        "MARY'S SALON",
        "CODY ANDERSON",
        "JOSE DBA JOSE'S TACO STAND",
        "SMITH AUTO REPAIR",
        "GREEN LAWN LANDSCAPING",
        "JAMES CONSTRUCTION",
        "PARK AVE DENTAL CLINIC",
        "BOB'S TRUCKING",
    ]

    print("Testing multi-tier keyword filter:")
    print("-" * 80)
    for name in test_names:
        is_biz, reason, matched = is_business_name(name)
        label = "BUSINESS" if is_biz else "PERSON"
        print(f"  {name:40} -> {label:8} ({reason}) {matched}")

    # Apply the multi-tier keyword filter to all remaining records
    print("Applying multi-tier keyword filter...")
    print("(This may take a few minutes on large datasets...)\n")

    # Apply is_business_name to each BorrowerName
    results = ppp_zip_clean['BorrowerName'].apply(is_business_name)

    # Unpack the (bool, reason, keywords) tuples into separate columns
    ppp_zip_clean['has_business_keyword'] = results.apply(lambda x: x[0])
    ppp_zip_clean['filter_reason'] = results.apply(lambda x: x[1])
    ppp_zip_clean['matched_keywords_list'] = results.apply(lambda x: x[2])

    n_with_keyword = int(ppp_zip_clean['has_business_keyword'].sum())
    n_without_keyword = len(ppp_zip_clean) - n_with_keyword

    print("=" * 60)
    print("KEYWORD FILTER RESULTS")
    print("=" * 60)
    print(f"Total after special char filter: {len(ppp_zip_clean):>12,}")
    print(f"Business names (filtered out):   {n_with_keyword:>12,}")
    print(f"Person names (kept):             {n_without_keyword:>12,}")
    print(f"Removal rate:                    {n_with_keyword / len(ppp_zip_clean) * 100:>11.2f}%")

    print(f"\nKeyword filter tier breakdown:")
    tier_counts = ppp_zip_clean[ppp_zip_clean['has_business_keyword']]['filter_reason'].value_counts()
    for tier, count in tier_counts.items():
        print(f"  {tier:<25} {count:>10,}")

    # Split into person names and business names
    ppp_person_names = ppp_zip_clean[~ppp_zip_clean['has_business_keyword']].copy()
    ppp_business_names = ppp_zip_clean[ppp_zip_clean['has_business_keyword']].copy()

    print(f"Person names (no keywords): {len(ppp_person_names):,}")
    print(f"Business names (has keywords): {len(ppp_business_names):,}")

    # # Remove duplicate BorrowerName + BorrowerZip combinations (keep first occurrence)
    # # COMMENTED OUT: Deduplication is skipped so final summary uses pre-dedup data
    # before_dedup = len(ppp_person_names)
    #
    # # Count duplicates before removing
    # n_dupes_before = ppp_person_names.duplicated(subset=['BorrowerName', 'BorrowerZip'], keep='first').sum()
    #
    # ppp_deduped = ppp_person_names.drop_duplicates(subset=['BorrowerName', 'BorrowerZip'], keep='first').copy()
    # after_dedup = len(ppp_deduped)
    #
    # print("=" * 60)
    # print("DEDUPLICATION FILTER RESULTS")
    # print("=" * 60)
    # print(f"Before dedup:            {before_dedup:>12,}")
    # print(f"Duplicate rows removed:  {before_dedup - after_dedup:>12,}")
    # print(f"After dedup:             {after_dedup:>12,}")
    # print(f"Removal rate:            {(before_dedup - after_dedup) / before_dedup * 100:>11.2f}%")
    #
    # # Show duplicate count distribution before removal
    # dupe_counts = (ppp_person_names
    #                .groupby(['BorrowerName', 'BorrowerZip'])
    #                .size()
    #                .reset_index(name='count'))
    # dupe_multi = dupe_counts[dupe_counts['count'] > 1]
    # print(f"\nDuplicate pairs breakdown:")
    # print(f"  Unique name-zip pairs with duplicates: {len(dupe_multi):,}")
    # if len(dupe_multi) > 0:
    #     print(f"  Distribution of duplicate counts:")
    #     print(dupe_multi['count'].value_counts().sort_index().to_string())

    # Use ppp_person_names directly (no deduplication)
    ppp_deduped = ppp_person_names.copy()
    after_dedup = len(ppp_deduped)
    print("Deduplication step SKIPPED.")
    print(f"Records carried forward: {after_dedup:,}")

    # Get all matched keywords for analysis
    ppp_business_names['matched_keywords'] = ppp_business_names['BorrowerName'].apply(get_matched_keywords)

    # Count keyword frequency
    from collections import Counter
    all_keywords = []
    for keywords in ppp_business_names['matched_keywords']:
        all_keywords.extend(keywords)

    keyword_counts = Counter(all_keywords)

    print("\nTop 20 Most Frequent Business Keywords:")
    print("-" * 40)
    for keyword, count in keyword_counts.most_common(20):
        print(f"  {keyword:20} {count:>10,}")

    # Show sample of person names (kept)
    print("\nSample PERSON names (kept - no business keywords):")
    print("-" * 50)
    for name in ppp_person_names['BorrowerName'].head(15):
        print(f"  {name}")

    # Show sample of business names (filtered out) with tier reason
    print("\nSample BUSINESS names (filtered out):")
    print("-" * 80)
    for idx, row in ppp_business_names.head(15).iterrows():
        name = row['BorrowerName']
        reason = row['filter_reason']
        keywords = row['matched_keywords']
        print(f"  {name:45} {reason:20} [{', '.join(keywords)}]")

    print("=" * 60)
    print("PIPELINE SUMMARY (All Filters)")
    print("=" * 60)
    print(f"\n1. Raw data records (all files):        {len(ppp_raw):>12,}")
    print(f"2. After first draw filter (PPP):        {after_first_draw:>12,}")
    print(f"3. After date filter (< Feb 24, 2021):   {after_date_filter:>12,}")
    print(f"4. After Race filter:                    {after_race:>12,}")
    print(f"5. After Zip filter:                     {after_zip:>12,}")
    print(f"6a. After special char filter:           {after_special:>12,}")
    print(f"6b. After NaN/NULL name filter:          {after_null:>12,}")
    print(f"7. After keyword filter (person names):  {n_without_keyword:>12,}")
    print(f"8. Deduplication:                        {'SKIPPED':>12}")
    print(f"   Final record count:                   {len(ppp_deduped):>12,}")
    print(f"\nOverall reduction: {len(ppp_raw) - len(ppp_deduped):,} records removed ({(len(ppp_raw) - len(ppp_deduped)) / len(ppp_raw) * 100:.2f}%)")

    print(f"\n{'=' * 60}")
    print("KEYWORD FILTER BREAKDOWN")
    print("=" * 60)
    tier_counts = ppp_zip_clean[ppp_zip_clean['has_business_keyword']]['filter_reason'].value_counts()
    for tier, count in tier_counts.items():
        print(f"  {tier:<25} {count:>10,}")

    # ── Remap Race categories ──
    # See markdown cell above for rationale
    RACE_REMAP = {
        'Native Hawaiian or Other Pacific Islander': 'Asian',
        'Puerto Rican': 'Hispanic or Latino',
        'American Indian or Alaska Native': 'Other',
        'Eskimo & Aleut': 'Other',
        'Multi Group': 'Other',
    }
    before_remap = ppp_deduped['Race'].value_counts()

    # Tag Puerto Rican rows BEFORE remapping Race (so we can update their Ethnicity)
    pr_rows = ppp_deduped['Race'] == 'Puerto Rican'
    ppp_deduped['Race'] = ppp_deduped['Race'].replace(RACE_REMAP)
    # Puerto Rican → Hispanic: also update Ethnicity so downstream logic captures them
    ppp_deduped.loc[pr_rows, 'Ethnicity'] = 'Hispanic or Latino'
    after_remap = ppp_deduped['Race'].value_counts()

    print("RACE REMAPPING")
    print("=" * 60)
    print("  Native Hawaiian or Other Pacific Islander  →  Asian")
    print("  Puerto Rican                               →  Hispanic or Latino")
    print("  American Indian or Alaska Native            →  Other")
    print("  Eskimo & Aleut                              →  Other")
    print("  Multi Group                                 →  Other")
    print(f"\nRace distribution after remapping:")
    for cat, count in after_remap.items():
        print(f"  {cat:<45} {count:>10,} ({count/len(ppp_deduped)*100:>5.1f}%)")

    # ── Create combined Race_Ethnicity variable ──
    def assign_race_ethnicity(row):
        ethnicity = row['Ethnicity']
        race = row['Race']
        if ethnicity == 'Hispanic or Latino':
            return 'Hispanic or Latino'
        elif ethnicity == 'Unknown/NotStated':
            return f"{race} (Ethnicity Unknown)"
        else:
            return race

    ppp_deduped['Race_Ethnicity'] = ppp_deduped.apply(assign_race_ethnicity, axis=1)

    print(f"\n{'=' * 60}")
    print("CLEANED DATA SUMMARY STATISTICS (NO DEDUPLICATION)")
    print("=" * 60)
    print(f"\nTotal records: {len(ppp_deduped):,}")

    # ── Race_Ethnicity combined distribution ──
    print(f"\n{'=' * 60}")
    print("RACE_ETHNICITY COMBINED DISTRIBUTION")
    print("=" * 60)
    re_dist = ppp_deduped['Race_Ethnicity'].value_counts()
    for re_cat, count in re_dist.items():
        print(f"  {re_cat:<50} {count:>10,} ({count/len(ppp_deduped)*100:>5.1f}%)")

    # ── Simplified Race_Ethnicity ──
    def assign_race_ethnicity_simple(row):
        ethnicity = row['Ethnicity']
        race = row['Race']
        if ethnicity == 'Hispanic or Latino':
            return 'Hispanic or Latino'
        else:
            return race

    ppp_deduped['Race_Ethnicity_Simple'] = ppp_deduped.apply(assign_race_ethnicity_simple, axis=1)

    print(f"\n{'=' * 60}")
    print("RACE_ETHNICITY SIMPLIFIED (Hispanic overrides race)")
    print("=" * 60)
    re_simple = ppp_deduped['Race_Ethnicity_Simple'].value_counts()
    for re_cat, count in re_simple.items():
        print(f"  {re_cat:<50} {count:>10,} ({count/len(ppp_deduped)*100:>5.1f}%)")

    # ── Race x Ethnicity crosstab ──
    print(f"\n{'=' * 60}")
    print("RACE x ETHNICITY CROSSTAB")
    print("=" * 60)
    crosstab = pd.crosstab(ppp_deduped['Race'], ppp_deduped['Ethnicity'], margins=True)
    print(crosstab.to_string())

    # ── Summary stats by Race_Ethnicity_Simple ──
    print(f"\n{'=' * 60}")
    print("LOAN AMOUNT BY RACE_ETHNICITY")
    print("=" * 60)
    if 'CurrentApprovalAmount' in ppp_deduped.columns:
        loan_by_race = ppp_deduped.groupby('Race_Ethnicity_Simple')['CurrentApprovalAmount'].agg(
            ['count', 'mean', 'median', 'std']
        ).sort_values('count', ascending=False)
        loan_by_race.columns = ['Count', 'Mean', 'Median', 'Std']
        for race_eth, row in loan_by_race.iterrows():
            print(f"  {race_eth:<50}")
            print(f"    N={row['Count']:>10,.0f}  Mean=${row['Mean']:>10,.2f}  Median=${row['Median']:>10,.2f}")

    # ── Gender distribution by Race_Ethnicity ──
    if 'Gender' in ppp_deduped.columns:
        print(f"\n{'=' * 60}")
        print("GENDER DISTRIBUTION BY RACE_ETHNICITY")
        print("=" * 60)
        gender_race = pd.crosstab(
            ppp_deduped['Race_Ethnicity_Simple'], 
            ppp_deduped['Gender'], 
            normalize='index'
        ) * 100
        print(gender_race.round(1).to_string())

    # ── BusinessType distribution ──
    print(f"\n{'=' * 60}")
    print("BUSINESS TYPE DISTRIBUTION")
    print("=" * 60)
    btype_dist = ppp_deduped['BusinessType'].value_counts()
    for btype, count in btype_dist.items():
        print(f"  {btype:<40} {count:>10,} ({count/len(ppp_deduped)*100:>5.1f}%)")

    # ── Overall Gender distribution ──
    if 'Gender' in ppp_deduped.columns:
        print(f"\n{'=' * 60}")
        print("OVERALL GENDER DISTRIBUTION")
        print("=" * 60)
        gender_dist = ppp_deduped['Gender'].value_counts(dropna=False)
        for gender, count in gender_dist.items():
            label = str(gender) if pd.notna(gender) else "Missing"
            print(f"  {label:<30} {count:>10,} ({count/len(ppp_deduped)*100:>5.1f}%)")

    # ── Loan amount statistics ──
    if 'CurrentApprovalAmount' in ppp_deduped.columns:
        print(f"\n{'=' * 60}")
        print("OVERALL LOAN AMOUNT STATISTICS")
        print("=" * 60)
        loan_stats = ppp_deduped['CurrentApprovalAmount'].describe()
        print(f"  Count:    {loan_stats['count']:>12,.0f}")
        print(f"  Mean:     ${loan_stats['mean']:>12,.2f}")
        print(f"  Median:   ${loan_stats['50%']:>12,.2f}")
        print(f"  Std:      ${loan_stats['std']:>12,.2f}")
        print(f"  Min:      ${loan_stats['min']:>12,.2f}")
        print(f"  Max:      ${loan_stats['max']:>12,.2f}")

    # Date range
    print(f"\nDate range:")
    print(f"  Earliest: {ppp_deduped['DateApproved'].min()}")
    print(f"  Latest:   {ppp_deduped['DateApproved'].max()}")

    # State distribution (top 10)
    if 'BorrowerState' in ppp_deduped.columns:
        print(f"\nTop 10 states:")
        state_dist = ppp_deduped['BorrowerState'].value_counts().head(10)
        for state, count in state_dist.items():
            print(f"  {state:<10} {count:>10,} ({count/len(ppp_deduped)*100:>5.1f}%)")

    # ── Save results ──
    output_person = os.path.join(intermediate_data_path, "PPP_person_names_filtered.csv")
    output_business = os.path.join(intermediate_data_path, "PPP_business_names_filtered.csv")

    ppp_deduped.to_csv(output_person, index=False)
    ppp_business_names.to_csv(output_business, index=False)

    print(f"\n{'=' * 60}")
    print("FILES SAVED")
    print("=" * 60)
    print(f"  Person names:   {output_person}")
    print(f"    Records: {len(ppp_deduped):,}")
    print(f"  Business names: {output_business}")
    print(f"    Records: {len(ppp_business_names):,}")
    print(f"\n{'=' * 60}")
    print("DONE!")
    print("=" * 60)



if __name__ == "__main__":
    main(_find_project_root(Path(__file__).resolve()))
