"""Parse PPP borrower person names into name parts and final analysis rows."""

from pathlib import Path
import os
import re

import numpy as np
import pandas as pd
try:
    from nameparser import HumanName
except ImportError as exc:
    raise ImportError(
        "The nameparser package is required. Install dependencies from requirements.txt."
    ) from exc


def _find_project_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "Data").is_dir() and (path / "src").is_dir():
            return path
    raise FileNotFoundError("Could not find project root containing Data/ and src/.")


def main(project_root: Path, ppp_person_names: pd.DataFrame) -> None:
    project_root = Path(project_root).resolve()
    cleaned_data_path = project_root / "Data" / "interim" / "processed_PPP"
    cleaned_data_path.mkdir(parents=True, exist_ok=True)

    print(f"Project root: {project_root}")

    ppp = ppp_person_names.copy()
    source_label = "raw merge / keyword filter step"
    print(f"Loaded {len(ppp):,} rows from {source_label}")
    print(f"Columns: {list(ppp.columns)}")
    print(ppp.head(3))

    # Drop any pre-existing name-parsed columns from prior runs
    name_cols = ['first_name', 'middle_name', 'last_name', 'suffix', 'credentials', 'parse_flag']
    existing = [c for c in name_cols if c in ppp.columns]
    if existing:
        print(f"\nDropping pre-existing columns from prior run: {existing}")
        ppp = ppp.drop(columns=existing)
    print(f"Shape after cleanup: {ppp.shape}")

    # ── Summary of imported names ───────────────────────────────────
    print("=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"Total names imported: {len(ppp):,}")
    print(f"  Source: {source_label}")
    print(f"\nUnique BorrowerNames:  {ppp['BorrowerName'].nunique():,}")
    print(f"Missing BorrowerName:  {ppp['BorrowerName'].isna().sum():,}")
    print(f"Duplicate loan rows:   {ppp.duplicated(subset='LoanNumber').sum():,}")

    # ── Professional credentials to strip BEFORE nameparser sees the name ──────
    # These are NOT generational suffixes (JR/SR/III) — nameparser handles those.
    # We remove credentials separately so they don't confuse name parsing.
    # ORDER MATTERS: longer patterns must come before shorter ones that are substrings
    #   e.g. ODS before OD, PLC before PL, FACS before any sub-match, PSYD before PS
    CRED_PATTERN = re.compile(
        r'\b('
        # ── Medical / Dental ──
        r'D\.?D\.?S\.?'         # DDS / D.D.S.
        r'|D\.?M\.?D\.?'        # DMD / D.M.D.
        r'|M\.?D\.?'            # MD  / M.D.
        r'|D\.?O\.?'            # DO  / D.O.
        r'|D\.?P\.?M\.?'        # DPM
        r'|D\.?P\.?T\.?'        # DPT (Doctor of Physical Therapy)
        r'|O\.?D\.?S\.?'        # ODS (before OD)
        r'|O\.?D\.?'            # OD
        r'|D\.?V\.?M\.?'        # DVM
        r'|D\.?R\.?'            # DR / Dr. (title prefix)
        r'|D\.?C\.?'            # DC (chiropractor)
        r'|N\.?D\.?'            # ND (Naturopathic Doctor)
        r'|PHARMD'              # PharmD (Doctor of Pharmacy)
        # ── Mental health / Counseling ──
        r'|PSY\.?D\.?'          # PsyD / PSY.D. (before PS)
        r'|L\.?C\.?S\.?W\.?'    # LCSW
        r'|L\.?M\.?F\.?T\.?'    # LMFT
        r'|L\.?C\.?P\.?C\.?'    # LCPC (before LPC)
        r'|L\.?M\.?H\.?C\.?'    # LMHC (Licensed Mental Health Counselor)
        r'|L\.?M\.?H\.?P\.?'    # LMHP (Licensed Mental Health Practitioner)
        r'|L\.?P\.?C\.?'        # LPC (Licensed Professional Counselor)
        r'|L\.?P\.?A\.?'        # LPA (Licensed Psychological Associate)
        r'|C\.?G\.?P\.?'        # CGP (Certified Group Psychotherapist)
        # ── Nursing / Allied health ──
        r'|C\.?R\.?N\.?A\.?'    # CRNA (Cert. Registered Nurse Anesthetist)
        r'|R\.?N\.?'            # RN
        r'|N\.?P\.?'            # NP
        r'|P\.?T\.?'            # PT (physical therapist)
        r'|L\.?M\.?T\.?'        # LMT (Licensed Massage Therapist)
        r'|C\.?M\.?T\.?'        # CMT (Certified Massage Therapist)
        r'|L\.?A\.?C\.?'        # LAC / L.AC. (Licensed Acupuncturist)
        r'|P\.?C\.?S\.?'        # PCS (Pediatric Clinical Specialist) — before PS
        # ── Business / Accounting / Finance ──
        r'|C\.?P\.?A\.?'        # CPA / C.P.A.
        r'|C\.?F\.?P\.?'        # CFP (Certified Financial Planner)
        r'|C\.?H\.?F\.?C\.?'    # CHFC (Chartered Financial Consultant)
        r'|C\.?L\.?U\.?'        # CLU (Chartered Life Underwriter)
        r'|E\.?A\.?'            # EA (Enrolled Agent)
        r'|M\.?B\.?A\.?'        # MBA
        # ── Academic ──
        r'|P\.?H\.?D\.?'        # PhD / Ph.D.
        r'|E\.?D\.?D\.?'        # EdD / Ed.D. (Doctor of Education) — before MSED
        r'|M\.?S\.?E\.?D\.?'    # MSED (Master of Science in Education) — before MS
        r'|M\.?S\.?'            # MS / M.S. (Master of Science)
        r'|M\.?P\.?H\.?'        # MPH (Master of Public Health)
        r'|M\.?ED\.?'           # M.Ed. (Master of Education)
        # ── Legal ──
        r'|ESQUIRE'             # Esquire (full word, before ESQ)
        r'|E\.?S\.?Q\.?'        # ESQ
        r'|L\.?L\.?M\.?'        # LLM (Master of Laws)
        r'|J\.?D\.?'            # JD / J.D. (Juris Doctor)
        # ── Business entity suffixes ──
        r'|L\.?L\.?C\.?'        # LLC / L.L.C.
        r'|L\.?T\.?D\.?'        # LTD / L.T.D.
        r'|I\.?N\.?C\.?'        # INC / I.N.C.
        r'|C\.?O\.?R\.?P\.?'    # CORP / C.O.R.P.
        r'|L\.?C\.?'            # LC / L.C. (must come AFTER LLC, LCPC, LCSW, LPC, etc.)
        # ── Professional corporation / entity ──
        r'|PMC'                 # PMC (Professional Medical Corporation)
        r'|P\.?S\.?C\.?'        # PSC (Professional Service Corp) — before PS
        r'|C\.?S\.?P\.?'        # CSP (Certified Speaking Professional)
        r'|A\.?P\.?D\.?C\.?'    # APDC — before APC
        r'|A\.?P\.?C\.?'        # APC (professional corporation)
        r'|F\.?A\.?C\.?S\.?'    # FACS (Fellow of Am. College of Surgeons)
        r'|P\.?S\.?'            # PS (professional services)
        r'|P\.?A\.?'            # PA (professional association)
        r'|P\.?L\.?C\.?'        # PLC (professional limited company) — before PL
        r'|P\.?L\.?'            # PL  (professional limited)
        r'|S\.?C\.?'            # SC (service corporation)
        # ── Other ──
        r'|L\.?S\.?'            # LS
        r'|INDEPENDENT\s+CONTRACTOR'  # Job description appearing after name
        r'|SOLE\s+PROPRIETOR'   # Job description appearing after name
        r'|CONSULTANT'          # Occupational title appearing after name
        r')\b',
        flags=re.IGNORECASE
    )

    # ── Spaced credential normalization patterns ───────────────────────────────
    # Some names have credentials with spaces between letters: "M D" instead of "MD"
    # We collapse these BEFORE running CRED_PATTERN so the regex can match them.
    SPACED_CRED_PATTERNS = [
        # 4-letter credentials
        (r'\bL\s+M\s+H\s+C\b',  'LMHC'),
        (r'\bL\s+M\s+H\s+P\b',  'LMHP'),
        (r'\bC\s+H\s+F\s+C\b',  'CHFC'),
        (r'\bM\s+S\s+E\s+D\b',  'MSED'),
        (r'\bA\s+P\s+D\s+C\b',  'APDC'),
        (r'\bC\s+O\s+R\s+P\b',  'CORP'),
        # 3-letter credentials (must come before 2-letter to avoid partial matches)
        (r'\bD\s+D\s+S\b',  'DDS'),
        (r'\bD\s+M\s+D\b',  'DMD'),
        (r'\bD\s+V\s+M\b',  'DVM'),
        (r'\bC\s+P\s+A\b',  'CPA'),
        (r'\bP\s+H\s+D\b',  'PHD'),
        (r'\bD\s+P\s+M\b',  'DPM'),
        (r'\bD\s+P\s+T\b',  'DPT'),
        (r'\bO\s+D\s+S\b',  'ODS'),
        (r'\bA\s+P\s+C\b',  'APC'),
        (r'\bE\s+S\s+Q\b',  'ESQ'),
        (r'\bL\s+M\s+T\b',  'LMT'),
        (r'\bC\s+F\s+P\b',  'CFP'),
        (r'\bL\s+P\s+C\b',  'LPC'),
        (r'\bC\s+L\s+U\b',  'CLU'),
        (r'\bC\s+M\s+T\b',  'CMT'),
        (r'\bM\s+P\s+H\b',  'MPH'),
        (r'\bM\s+B\s+A\b',  'MBA'),
        (r'\bC\s+S\s+P\b',  'CSP'),
        (r'\bP\s+M\s+C\b',  'PMC'),
        (r'\bL\s+L\s+M\b',  'LLM'),
        (r'\bC\s+G\s+P\b',  'CGP'),
        (r'\bP\s+S\s+C\b',  'PSC'),
        (r'\bP\s+C\s+S\b',  'PCS'),
        (r'\bL\s+L\s+C\b',  'LLC'),
        (r'\bL\s+T\s+D\b',  'LTD'),
        (r'\bI\s+N\s+C\b',  'INC'),
        (r'\bE\s+D\s+D\b',  'EDD'),
        # 2-letter credentials — use lookaround to avoid matching initials mid-name
        (r'(?<=[\s,])\s*M\s+D\s*(?=[,.\s]|$)',  ' MD'),
        (r'(?<=[\s,])\s*D\s+O\s*(?=[,.\s]|$)',  ' DO'),
        (r'(?<=[\s,])\s*D\s+C\s*(?=[,.\s]|$)',  ' DC'),
        (r'(?<=[\s,])\s*P\s+A\s*(?=[,.\s]|$)',  ' PA'),
        (r'(?<=[\s,])\s*P\s+T\s*(?=[,.\s]|$)',  ' PT'),
        (r'(?<=[\s,])\s*R\s+N\s*(?=[,.\s]|$)',  ' RN'),
        (r'(?<=[\s,])\s*N\s+P\s*(?=[,.\s]|$)',  ' NP'),
        (r'(?<=[\s,])\s*P\s+L\s*(?=[,.\s]|$)',  ' PL'),
        (r'(?<=[\s,])\s*O\s+D\s*(?=[,.\s]|$)',  ' OD'),
        (r'(?<=[\s,])\s*L\s+S\s*(?=[,.\s]|$)',  ' LS'),
        (r'(?<=[\s,])\s*E\s+A\s*(?=[,.\s]|$)',  ' EA'),
        (r'(?<=[\s,])\s*M\s+S\s*(?=[,.\s]|$)',  ' MS'),
        (r'(?<=[\s,])\s*N\s+D\s*(?=[,.\s]|$)',  ' ND'),
        (r'(?<=[\s,])\s*J\s+D\s*(?=[,.\s]|$)',  ' JD'),
        (r'(?<=[\s,])\s*L\s+C\s*(?=[,.\s]|$)',  ' LC'),
        (r'(?<=[\s,])\s*S\s+C\s*(?=[,.\s]|$)',  ' SC'),
    ]

    # Generational suffixes that nameparser handles — do NOT strip these as credentials
    GENERATIONAL = {'JR', 'JR.', 'SR', 'SR.', 'II', 'III', 'IV', 'V', '2ND', '3RD', '4TH'}

    # Descriptor / profession words that appear next to colons as labels, not person names.
    # If one side of the colon (≤3 words) contains these, keep the OTHER side.
    # e.g. "INDIVIDUAL ARTIST: KAO YANG" → before has ARTIST → keep "KAO YANG"
    # e.g. "CLIFFORD R ANDERSON: UBER DRIVER" → after has DRIVER → keep "CLIFFORD R ANDERSON"
    DESCRIPTOR_WORDS = {
        'INDIVIDUAL', 'INDEPENDENT', 'ARTIST', 'CONTRACTOR', 'REALTOR',
        'DRIVER', 'UBER', 'TEACHER', 'THERAPIST', 'SPECIALIST',
    }


    def _normalize_spaced_creds(name_str):
        """Collapse spaced credentials like 'M D' -> 'MD' before regex matching."""
        # Normalize comma-separated truncated credentials: ED,D → EDD
        name_str = re.sub(r'\bED[,.]D\b', 'EDD', name_str, flags=re.IGNORECASE)
        for pattern, replacement in SPACED_CRED_PATTERNS:
            name_str = re.sub(pattern, replacement, name_str, flags=re.IGNORECASE)
        return name_str


    def parse_borrower_name(name):
        """
        Split a BorrowerName into components + a parse_flag for downstream QC.

        Returns: first_name, middle_name, last_name, suffix, credentials, parse_flag

        parse_flag values:
          clean          — standard 2-4 word personal name
          has_credentials — credentials stripped, name parsed
          single_word    — could not split into first/last; entire string in last_name
          multi_person   — contains "AND"; only first person parsed
          long_name      — 5+ words after credential AND suffix removal
        """
        if pd.isna(name) or str(name).strip() == '':
            return pd.Series({
                'first_name': '', 'middle_name': '',
                'last_name': '', 'suffix': '', 'credentials': '',
                'parse_flag': 'clean'
            })

        name_str = str(name).strip()
        name_upper = name_str.upper()
        parse_flag = 'clean'

        # ── Step 0b: Handle colon-separated labels ─────────────────────────────
        if ':' in name_str:
            name_str = name_str.replace('::', ':')
            name_str = re.sub(r'^\s*:\s*', '', name_str)
            name_str = re.sub(r'\s*:\s*$', '', name_str)
            if ':' in name_str:
                before, after = name_str.split(':', 1)
                before, after = before.strip(), after.strip()
                before_words = before.split()
                after_words = after.split()
                before_set = set(w.upper() for w in before_words)
                after_set = set(w.upper() for w in after_words)
                before_is_label = (len(before_words) <= 3
                                   and bool(before_set & DESCRIPTOR_WORDS))
                after_is_label = (len(after_words) <= 3
                                  and bool(after_set & DESCRIPTOR_WORDS))
                if before_is_label and after and not after_is_label:
                    name_str = after
                elif after_is_label and before and not before_is_label:
                    name_str = before
                else:
                    name_str = name_str.replace(':', ' ')
            name_str = re.sub(r'\s{2,}', ' ', name_str).strip()
            name_upper = name_str.upper()

        # ── Step 1: Handle multi-person "AND" names ────────────────────────────
        if re.search(r'\bAND\b', name_upper):
            parse_flag = 'multi_person'
            parts = re.split(r'\bAND\b', name_str, maxsplit=1, flags=re.IGNORECASE)
            first_part = parts[0].strip()
            second_part = parts[1].strip() if len(parts) > 1 else ''

            first_words = first_part.split()
            second_words = second_part.split()

            if len(first_words) == 1 and len(second_words) >= 2:
                name_str = first_words[0] + ' ' + second_words[-1]
            elif len(first_words) >= 2:
                name_str = first_part
            else:
                name_str = first_part

        # ── Step 2: Normalize spaced credentials ───────────────────────────────
        name_str = _normalize_spaced_creds(name_str)

        # ── Step 3: Pull out professional credentials ──────────────────────────
        cred_matches = CRED_PATTERN.findall(name_str)
        credentials  = ' '.join(cred_matches).upper()
        clean_name   = CRED_PATTERN.sub('', name_str)

        if credentials and parse_flag == 'clean':
            parse_flag = 'has_credentials'

        # ── Step 4: Clean up leftover punctuation / extra whitespace ────────────
        clean_name = re.sub(r'(?<![A-Za-z])\.(?![A-Za-z])', ' ', clean_name)
        clean_name = re.sub(r',\s*,', ',', clean_name)
        clean_name = re.sub(r',\s*,', ',', clean_name)
        clean_name = re.sub(r'[,\s]+$', '', clean_name)
        clean_name = re.sub(r'^\s*[,]\s*', '', clean_name)
        clean_name = re.sub(r'\s{2,}', ' ', clean_name).strip()

        # ── Step 4b: Strip residual comma-separated tokens ─────────────────────
        if credentials:
            comma_parts = [p.strip() for p in clean_name.split(',') if p.strip()]
            if len(comma_parts) > 1:
                first_part_words = comma_parts[0].split()
                if len(first_part_words) >= 2:
                    name_keep = [comma_parts[0]]
                    residual_creds = []
                    for part in comma_parts[1:]:
                        if part.strip().upper() in GENERATIONAL:
                            name_keep.append(part)
                        else:
                            residual_creds.append(part.strip().upper())
                    if residual_creds:
                        credentials = credentials + ' ' + ' '.join(residual_creds)
                        clean_name = ', '.join(name_keep)

        # ── Step 5: Handle single-word names ───────────────────────────────────
        words = clean_name.split()
        if len(words) <= 1:
            return pd.Series({
                'first_name': '',
                'middle_name': '',
                'last_name': clean_name.upper(),
                'suffix': '',
                'credentials': credentials,
                'parse_flag': 'single_word'
            })

        # ── Step 6: Flag long names (5+ words after removing suffixes) ─────────
        # Count non-suffix words to decide if this is a long name
        non_suffix_words = [w for w in words if w.upper().rstrip('.') not in
                            {'JR', 'SR', 'II', 'III', 'IV', 'V', '2ND', '3RD', '4TH'}]
        if len(non_suffix_words) >= 5:
            parse_flag = 'long_name'

        # ── Step 6b: Protect NULL/NA from nameparser ───────────────────────────
        _null_placeholder = False
        _na_placeholder = False
        if re.search(r'\bNULL\b', clean_name, re.IGNORECASE):
            clean_name = re.sub(r'\bNULL\b', 'NULLXYZ', clean_name, flags=re.IGNORECASE)
            _null_placeholder = True
        if re.search(r'\bNA\b', clean_name, re.IGNORECASE):
            clean_name = re.sub(r'\bNA\b', 'NAXYZ', clean_name, flags=re.IGNORECASE)
            _na_placeholder = True

        # ── Step 7: Parse with nameparser ──────────────────────────────────────
        parsed = HumanName(clean_name)

        # ── Step 8: Recover titles consumed by nameparser ──────────────────────
        first  = str(parsed.first).upper()
        middle = str(parsed.middle).upper()
        last   = str(parsed.last).upper()
        suffix = str(parsed.suffix).upper()
        title  = str(parsed.title).strip().upper()

        if title and not first:
            first = title
        elif title and first and not last:
            last = first
            first = title
        elif title and first and last and not middle:
            middle = first
            first = title

        # ── Step 8b: Restore NULL/NA placeholders ──────────────────────────────
        if _null_placeholder:
            first  = first.replace('NULLXYZ', 'NULL')
            middle = middle.replace('NULLXYZ', 'NULL')
            last   = last.replace('NULLXYZ', 'NULL')
            suffix = suffix.replace('NULLXYZ', 'NULL')
        if _na_placeholder:
            first  = first.replace('NAXYZ', 'NA')
            middle = middle.replace('NAXYZ', 'NA')
            last   = last.replace('NAXYZ', 'NA')
            suffix = suffix.replace('NAXYZ', 'NA')

        return pd.Series({
            'first_name':  first,
            'middle_name': middle,
            'last_name':   last,
            'suffix':      suffix,
            'credentials': credentials,
            'parse_flag':  parse_flag,
        })


    # ── Quick sanity check ─────────────────────────────────────────────────────
    test_cases = [
        "JOHN SMITH",
        "JOHN M. SMITH",
        "JOHN SMITH JR",
        "WILLIAM B. COLLIER, JR., DMD",
        "TIMOTHY M. LETHIN, DDS APC",
        "DAVID A. ALBERTSON, DDS",
        "STEVEN E HOFSTAD D.D.S.",
        "JOSE MARIA GARCIA RODRIGUEZ",
        "JOHN DE LA CRUZ",
        "MARIA GARCIA-LOPEZ",
        "DWAIN A. FOSTER, SR.",
        "DALE J TROMBLEY II MD",
        "SMITH, JOHN",
        "H. RAY HIX, DDS",
        "MARK AND ANGIE HIXSON",
        "JOHN AND MARY SMITH",
        "MICHAELMAYNARD",
        "ROBERT J ANDERSON DVM",
        "SARAH JANE WILLIAMS PT",
        # Credential fixes
        "PHUONG-UYEN NGOC LE D.M.D. P.L.",
        "IVAN RAMIREZ, M D , P A",
        "REKHA MANGHNANI M D",
        "J TIM RUSSIN D D S P A",
        "TRICIA R. ANDREWS, M.D., PL",
        "BRYANT A. TOTH, M.D., F.A.C.S.",
        "RONALD D. ROGERS, D.M.D.",
        "CAROL A. LEITNER, M.D.",
        # Title recovery + CONSULTANT + DR
        "MASTER DONUTS",
        "SHEIKH KANNEH",
        "RICHARD H. WATSON, CONSULTANT",
        "DR JOHN SMITH",
        "DR. JANE DOE",
        # Credential tests
        "MICHAEL J GUNSON, DDS, MD, PMC",
        "GREGORY J ALLEN, MD, PMC",
        "JOHN SMITH, CFP, CLU",
        "JANE DOE LMT",
        "BOB JONES, PSYD",
        "ALICE WANG, CRNA",
        # Too-many-credentials (residual stripping)
        "BRIAN M. JONES, CPA, CFP, CLU AGENT",
        "SCOTT E. KEITH, DDS, MS, APDC",
        "ONEIL CULVER, M.D., F.A.C.S., GENERAL SURGERY",
        "C. ALEXANDRA CHANG, D.D.S., M.S., A PROF",
        "ELIZABETH KRAINER, PH.D., PSY.D., CGP",
        "ANTHONY R COLLETTI, CFP, CLU, CHFC",
        "MARCIA J KESNER, PHD, LPC, LMHC",
        "CHRISTOPHER K. BRAUN, MBA, JD, LLM",
        "FANNY YACAMAN, DDS, MS, MSED",
        "JACQUELINE J. VINEYARD, D.M.D., M.S., LL",
        "CATHIE DUNAL, MD, MPH, SC",
        "MICHAEL R WESTMAN, DDS, MS, SC",
        "PAUL E. TRAN, DDS, MS, PSC",
        "MARY EILEEN MURNEY, PT, MS, PCS",
        # NULL / NA names
        "JOSHUA NULL",
        "WILLIAM SCOTT NULL",
        "VIVIAN NA",
        "YOUNG NA",
        # Colon-separated labels (both directions)
        "INDIVIDUAL ARTIST: KAO YANG",
        ": ABRIL GERMAN",
        "CLIFFORD R ANDERSON: UBER DRIVER",
        "MKT: GRAFTON",
        # Long name with credentials (should now be flagged long_name)
        "CENTRO DE GINECOLOGIA Y OBSTETRICIA DR CARLOS A FONSECA SALG",
        "DALE J TROMBLEY II MD ALASKA PRIVATE PRACTICE",
        # Business entity suffixes
        "SAM'S GOURMET JAMS, LLC",
        "AVA'S LOWCOUNTRY CUISINE LLC",
        "JOHN SMITH INC",
        "JANE DOE LTD",
        "BOB JONES CORP",
        "JAMES TZU-LUN WEN L.L.C",
        # Independent contractor / sole proprietor / Ed.D.
        "BENJAMIN C. WOLFE, INDEPENDENT CONTRACTOR",
        "THOMAS E. GRAY SOLE PROPRIETOR",
        "ALICE C. MOORE ED,D",
        "REBECCA A. JEFFERS M.ED., EDD",
    ]

    cols = ['first_name', 'middle_name', 'last_name', 'suffix', 'credentials', 'parse_flag']
    print(f"{'Original':<65} {'First':<15} {'Middle':<10} {'Last':<18} {'Suffix':<8} {'Creds':<20} {'Flag'}")
    print("-" * 155)
    for t in test_cases:
        r = parse_borrower_name(t)
        print(f"{t:<65} {r.first_name:<15} {r.middle_name:<10} {r.last_name:<18} {r.suffix:<8} {r.credentials:<20} {r.parse_flag}")

    # ── Apply to full dataset ────────────────────────────────────────
    print(f"Parsing {len(ppp):,} borrower names...")

    name_parsed = ppp['BorrowerName'].apply(parse_borrower_name)
    ppp = pd.concat([ppp, name_parsed], axis=1)

    print("Done.\n")

    # ── Hardcoded MA suffix corrections ─────────────────────────────
    # MA in suffix is ambiguous: Chinese surname, credential (Master of Arts),
    # or state abbreviation. Corrections based on manual review of all 27 names.
    ma_suffix = ppp['suffix'].str.contains(r'\bMA\b', na=False)
    bn_upper  = ppp['BorrowerName'].str.upper()

    # --- Category 1: MA is the last name (Chinese surname) ---
    ma_lastname_patterns = [
        'LINH T MA', 'DAVID L MA', 'CHANG CHIEH MA', 'IN KYOUNG MA',
        'ADRIAN ON NING MA', 'CHAGRIN FALLS MA'
    ]
    ma_ln_mask = ma_suffix & bn_upper.str.contains('|'.join(ma_lastname_patterns), na=False)
    if ma_ln_mask.any():
        # Shift: current last_name → append to middle_name, set last_name = MA
        ppp.loc[ma_ln_mask, 'middle_name'] = ppp.loc[ma_ln_mask].apply(
            lambda r: (r['middle_name'] + ' ' + r['last_name']).strip()
            if r['middle_name'] else r['last_name'], axis=1)
        ppp.loc[ma_ln_mask, 'last_name'] = 'MA'
        ppp.loc[ma_ln_mask, 'suffix'] = ppp.loc[ma_ln_mask, 'suffix'].str.replace(
            r',?\s*\bMA\b', '', regex=True).str.strip().str.strip(',').str.strip()

    # --- Category 2: MA is state abbreviation ---
    ma_state_mask = ma_suffix & bn_upper.str.contains('ENVIROSCAPE EROSION CONTROL MA', na=False)
    if ma_state_mask.any():
        ppp.loc[ma_state_mask, 'suffix'] = ppp.loc[ma_state_mask, 'suffix'].str.replace(
            r',?\s*\bMA\b', '', regex=True).str.strip().str.strip(',').str.strip()

    # --- Category 3: MA is credential (all remaining MA-in-suffix rows) ---
    ma_cred_mask = ma_suffix & ~ma_ln_mask & ~ma_state_mask
    if ma_cred_mask.any():
        ppp.loc[ma_cred_mask, 'credentials'] = ppp.loc[ma_cred_mask].apply(
            lambda r: (r['credentials'] + ' MA').strip() if r['credentials'] else 'MA', axis=1)
        ppp.loc[ma_cred_mask, 'suffix'] = ppp.loc[ma_cred_mask, 'suffix'].str.replace(
            r',?\s*\bMA\b', '', regex=True).str.strip().str.strip(',').str.strip()
        # Update parse_flag to has_credentials if it was clean
        clean_now_cred = ma_cred_mask & (ppp['parse_flag'] == 'clean')
        ppp.loc[clean_now_cred, 'parse_flag'] = 'has_credentials'

    print(f"MA corrections: {ma_ln_mask.sum()} as last_name, "
          f"{ma_cred_mask.sum()} as credential, {ma_state_mask.sum()} as state abbrev.")

    # Show corrected MA rows
    ma_all = ma_ln_mask | ma_state_mask | ma_cred_mask
    cols_show = ['BorrowerName', 'first_name', 'middle_name', 'last_name', 'suffix', 'credentials', 'parse_flag']
    if ma_all.any():
        print(f"\nCorrected MA rows ({ma_all.sum()}):")
        print(ppp.loc[ma_all, cols_show].to_string(index=False))

    # ── QC: parse_flag breakdown ──────────────────────────────────
    print(f"\n{'=' * 60}")
    print("PARSE FLAG BREAKDOWN")
    print("=" * 60)
    flag_counts = ppp['parse_flag'].value_counts()
    for flag, count in flag_counts.items():
        print(f"  {flag:<20} {count:>10,} ({count/len(ppp)*100:.2f}%)")

    # ── QC: empty name stats ──────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("NAME COMPLETENESS")
    print("=" * 60)
    empty_last = (ppp['last_name'] == '')
    print(f"Names with empty last_name:  {empty_last.sum():,} ({empty_last.mean()*100:.2f}%)")

    empty_first = (ppp['first_name'] == '')
    print(f"Names with empty first_name: {empty_first.sum():,} ({empty_first.mean()*100:.2f}%)")

    has_middle = (ppp['middle_name'] != '')
    print(f"Names with middle name/init: {has_middle.sum():,} ({has_middle.mean()*100:.2f}%)")

    has_suffix = (ppp['suffix'] != '')
    print(f"Names with suffix (JR/SR..): {has_suffix.sum():,} ({has_suffix.mean()*100:.2f}%)")

    has_creds = (ppp['credentials'] != '')
    print(f"Names with credentials:      {has_creds.sum():,} ({has_creds.mean()*100:.2f}%)")

    # ── QC: Name parts breakdown (clean + has_credentials) ─────────
    print(f"\n{'=' * 60}")
    print("NAME PARTS BREAKDOWN (clean + has_credentials only)")
    print("=" * 60)
    mask_good = ppp['parse_flag'].isin(['clean', 'has_credentials'])
    sub = ppp[mask_good].copy()

    def _count_name_parts(row):
        parts = 0
        for col in ['first_name', 'last_name', 'middle_name']:
            if str(row[col]).strip():
                parts += 1
        return parts

    sub['n_parts'] = sub.apply(_count_name_parts, axis=1)
    cols = ['BorrowerName', 'first_name', 'middle_name', 'last_name', 'suffix', 'credentials', 'parse_flag']

    for n in sorted(sub['n_parts'].unique()):
        count = (sub['n_parts'] == n).sum()
        print(f"\n  {n}-part names: {count:>10,} ({count/len(sub)*100:.2f}%)")
        sample = sub[sub['n_parts'] == n].sample(n=min(5, count), random_state=42)
        print(sample[cols].to_string(index=False))

    print(f"\n  Total:        {len(sub):>10,}")

    # ── Sample output per flag category ────────────────────────────
    for flag in sorted(ppp['parse_flag'].unique()):
        subset = ppp[ppp['parse_flag'] == flag]
        n_show = min(10, len(subset))
        print(f"\n{'=' * 60}")
        print(f"Sample: {flag} (n={len(subset):,})")
        print("=" * 60)
        print(subset[cols].sample(n=n_show, random_state=42).to_string(index=False))

    # ── Drop pre-existing chunk columns from prior runs ──────────────────────
    chunk_cols_existing = [c for c in ppp.columns if c.startswith('name_part_') or c == 'n_name_parts']
    if chunk_cols_existing:
        print(f"Dropping pre-existing chunk columns: {chunk_cols_existing}")
        ppp = ppp.drop(columns=chunk_cols_existing)

    # Suffixes to strip (same as GENERATIONAL, plus dotless variants for matching)
    SUFFIXES_TO_STRIP = {'JR', 'JR.', 'SR', 'SR.', 'II', 'III', 'IV', 'V', '2ND', '3RD', '4TH'}

    # ── Strip credentials AND suffixes, then split into chunks ───────────────
    def get_name_chunks(name):
        """
        Strip credentials and generational suffixes from BorrowerName,
        then return the remaining text chunks.
        Consecutive single-letter chunks are merged (e.g. S C → SC)
        and re-checked against credential patterns.
        Does NOT assign first/middle/last semantics — just splits by whitespace.
        """
        if pd.isna(name) or str(name).strip() == '':
            return []

        name_str = str(name).strip()

        # Handle colon-separated labels (same logic as parse_borrower_name)
        if ':' in name_str:
            name_str = name_str.replace('::', ':')
            name_str = re.sub(r'^\s*:\s*', '', name_str)
            name_str = re.sub(r'\s*:\s*$', '', name_str)
            if ':' in name_str:
                before, after = name_str.split(':', 1)
                before, after = before.strip(), after.strip()
                before_words = before.split()
                after_words = after.split()
                before_set = set(w.upper() for w in before_words)
                after_set = set(w.upper() for w in after_words)
                before_is_label = (len(before_words) <= 3
                                   and bool(before_set & DESCRIPTOR_WORDS))
                after_is_label = (len(after_words) <= 3
                                  and bool(after_set & DESCRIPTOR_WORDS))
                if before_is_label and after and not after_is_label:
                    name_str = after
                elif after_is_label and before and not before_is_label:
                    name_str = before
                else:
                    name_str = name_str.replace(':', ' ')
            name_str = re.sub(r'\s{2,}', ' ', name_str).strip()

        # Handle multi-person "AND" — keep first person only
        name_upper = name_str.upper()
        if re.search(r'\bAND\b', name_upper):
            parts = re.split(r'\bAND\b', name_str, maxsplit=1, flags=re.IGNORECASE)
            first_part = parts[0].strip()
            second_part = parts[1].strip() if len(parts) > 1 else ''
            first_words = first_part.split()
            second_words = second_part.split()
            if len(first_words) == 1 and len(second_words) >= 2:
                name_str = first_words[0] + ' ' + second_words[-1]
            elif len(first_words) >= 2:
                name_str = first_part
            else:
                name_str = first_part

        # Normalize spaced credentials and strip them
        name_str = _normalize_spaced_creds(name_str)
        cred_matches = CRED_PATTERN.findall(name_str)
        clean_name = CRED_PATTERN.sub('', name_str)

        # Clean up leftover punctuation
        clean_name = re.sub(r'(?<![A-Za-z])\.(?![A-Za-z])', ' ', clean_name)
        clean_name = re.sub(r',\s*,', ',', clean_name)
        clean_name = re.sub(r'[,\s]+$', '', clean_name)
        clean_name = re.sub(r'^\s*[,]\s*', '', clean_name)

        # Strip residual comma-separated tokens (likely missed credentials)
        if cred_matches:
            comma_parts = [p.strip() for p in clean_name.split(',') if p.strip()]
            if len(comma_parts) > 1:
                first_part_words = comma_parts[0].split()
                if len(first_part_words) >= 2:
                    name_keep = [comma_parts[0]]
                    for part in comma_parts[1:]:
                        if part.strip().upper() in GENERATIONAL:
                            pass  # drop suffixes too
                    clean_name = ', '.join(name_keep)

        # Remove remaining commas and periods, collapse whitespace
        clean_name = clean_name.replace(',', ' ').replace('.', ' ')
        clean_name = re.sub(r'\s{2,}', ' ', clean_name).strip()

        # Split into chunks
        chunks = clean_name.upper().split() if clean_name else []

        # Remove generational suffixes
        chunks = [c for c in chunks if c not in SUFFIXES_TO_STRIP]

        # Merge consecutive single-letter chunks → e.g. ['S', 'C'] → ['SC']
        merged = []
        i = 0
        while i < len(chunks):
            if len(chunks[i]) == 1 and chunks[i].isalpha():
                # Collect consecutive single letters
                run = [chunks[i]]
                j = i + 1
                while j < len(chunks) and len(chunks[j]) == 1 and chunks[j].isalpha():
                    run.append(chunks[j])
                    j += 1
                if len(run) > 1:
                    # Merge into one token
                    merged.append(''.join(run))
                else:
                    merged.append(run[0])
                i = j
            else:
                merged.append(chunks[i])
                i += 1

        # Re-run credential filter on merged chunks to catch things like SC, LC, LLC
        final = []
        for chunk in merged:
            # Check if the merged chunk is a credential
            if CRED_PATTERN.fullmatch(chunk):
                continue  # drop it — it's a credential
            final.append(chunk)

        return final


    # Apply to all rows
    print("Splitting names into chunks (stripping credentials + suffixes, merging single letters)...")
    chunks_series = ppp['BorrowerName'].apply(get_name_chunks)

    # Count parts
    ppp['n_name_parts'] = chunks_series.apply(len)

    # Create name_part_1, name_part_2, ... columns
    max_parts = ppp['n_name_parts'].max()
    print(f"Max chunks found: {max_parts}")

    for i in range(1, max_parts + 1):
        ppp[f'name_part_{i}'] = chunks_series.apply(
            lambda x, idx=i: x[idx - 1] if len(x) >= idx else ''
        )

    # ── Reclassify edge-case chunk counts ───────────────────────────
    # Names with <=1 chunk are effectively single-word; >=5 chunks are long names
    mask_single = (ppp['n_name_parts'] <= 1) & ppp['parse_flag'].isin(['clean', 'has_credentials'])
    ppp.loc[mask_single, 'parse_flag'] = 'single_word'
    mask_long = (ppp['n_name_parts'] >= 5) & ppp['parse_flag'].isin(['clean', 'has_credentials'])
    ppp.loc[mask_long, 'parse_flag'] = 'long_name'
    if mask_single.any() or mask_long.any():
        print(f"Reclassified: {mask_single.sum()} -> single_word, {mask_long.sum()} -> long_name")

    # ── Summary (clean + has_credentials only) ───────────────────────
    # Exclude single_word, multi_person, long_name from summary
    good_mask = ppp['parse_flag'].isin(['clean', 'has_credentials'])
    ppp_good = ppp[good_mask].copy()
    print(f"\nFiltered to clean + has_credentials: {len(ppp_good):,} / {len(ppp):,} rows")
    print(f"Excluded: single_word={((ppp['parse_flag']=='single_word').sum()):,}, "
          f"multi_person={((ppp['parse_flag']=='multi_person').sum()):,}, "
          f"long_name={((ppp['parse_flag']=='long_name').sum()):,}")

    print(f"\n{'=' * 60}")
    print("NAME CHUNKS BREAKDOWN (clean + has_credentials only)")
    print("(after stripping credentials + suffixes, merging single letters)")
    print("=" * 60)
    part_counts = ppp_good['n_name_parts'].value_counts().sort_index()
    for n_parts, count in part_counts.items():
        print(f"  {n_parts}-part names: {count:>10,} ({count / len(ppp_good) * 100:.2f}%)")
    print(f"  {'Total:':<14} {len(ppp_good):>10,}")

    # ── Show samples for each chunk count ────────────────────────────
    part_cols = ['BorrowerName', 'n_name_parts', 'parse_flag', 'suffix', 'credentials'] + [f'name_part_{i}' for i in range(1, min(max_parts + 1, 6))]
    for n_parts in sorted(ppp_good['n_name_parts'].unique()):
        subset = ppp_good[ppp_good['n_name_parts'] == n_parts]
        n_show = min(8, len(subset))
        print(f"\n--- {n_parts}-part names (n={len(subset):,}) ---")
        print(subset[part_cols].sample(n=n_show, random_state=42).to_string(index=False))

    # ── Race share and fintech share by race group ─────────────────
    # Use only clean + has_credentials names (267,212) — after cutting single names,
    # multi-person names, and long names.
    good_mask = ppp['parse_flag'].isin(['clean', 'has_credentials'])
    ppp_analysis = ppp[good_mask].copy()

    # Define fintech lender list (same as PPP_fintech_indicator.ipynb)
    fintech_lenders = [
        'Cross River Bank', 'Kabbage', 'Celtic Bank Corporation', 'Lendio',
        'WebBank', 'Customers Bank', 'Readycap Lending', 'Itria Ventures',
        'Intuit Financing', 'Newtek Small Business Finance', 'Fundbox',
        'MBE Capital Partners', 'FC Marketplace', 'Harvest Small Business Finance',
        'Fountainhead SBF', 'CRF Small Business Loan Company',
        'Sunrise Banks National Association', 'Accion', 'Fund-Ex Solutions Group',
        'The Bancorp Bank', 'Centerstone SBA Lending', 'Grow America Fund',
        'Evolve Bank and Trust', 'NBKC Bank', 'Immito', 'Loan Source',
        'BayBank', 'VelocitySBA',
    ]
    fintech_set = {name.strip().upper() for name in fintech_lenders}
    ppp['fintech'] = ppp['OriginatingLender'].str.strip().str.upper().isin(fintech_set).astype(int)
    ppp_analysis = ppp[good_mask].copy()

    # Define the five race groups in display order
    race_order = [
        'White',
        'Black or African American',
        'Hispanic or Latino',
        'Asian',
        'Other',
    ]
    race_col = 'Race_Ethnicity_Simple'
    total_n = len(ppp_analysis)

    print("=" * 75)
    print("RACE SHARE AND FINTECH SHARE BY RACE GROUP")
    print(f"(using clean + has_credentials names only, N={total_n:,})")
    print("=" * 75)
    print(f"\n{'Race Group':<32} {'N':>10} {'Race Share':>12} {'Fintech N':>11} {'Fintech %':>11}")
    print("-" * 75)

    for race in race_order:
        mask = ppp_analysis[race_col] == race
        n = mask.sum()
        race_share = n / total_n * 100
        fintech_n = ppp_analysis.loc[mask, 'fintech'].sum()
        fintech_pct = fintech_n / n * 100 if n > 0 else 0
        print(f"  {race:<30} {n:>10,} {race_share:>10.2f}%  {fintech_n:>10,} {fintech_pct:>9.2f}%")

    fintech_all = ppp_analysis['fintech'].sum()
    print("-" * 75)
    print(f"  {'Total':<30} {total_n:>10,} {100:>10.2f}%  {fintech_all:>10,} {fintech_all/total_n*100:>9.2f}%")

    print("Skipping full parsed dataset save; only final analysis rows are written.")
    print(f"Columns: {list(ppp.columns)}")
    print(f"\nName columns added: first_name, middle_name, last_name, suffix, credentials, parse_flag")
    print("\nDone!")

    # Save final subset used for analysis: clean + has_credentials only
    final_mask = ppp['parse_flag'].isin(['clean', 'has_credentials'])
    ppp_final = ppp[final_mask].copy()

    final_output_file = os.path.join(cleaned_data_path, "PPP_person_names_final.csv")
    ppp_final.to_csv(final_output_file, index=False)

    print(f"Saved {len(ppp_final):,} rows to {final_output_file}")
    print("Included parse_flag values:")
    print(ppp_final['parse_flag'].value_counts().to_string())
    print(f"Excluded {len(ppp) - len(ppp_final):,} rows with parse_flag outside clean/has_credentials")



if __name__ == "__main__":
    from PPP_raw_merge_keyword_filter import main as merge_keyword_filter

    root = _find_project_root(Path(__file__).resolve())
    main(root, merge_keyword_filter(root))
