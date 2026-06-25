import json

with open(
    "agreement_metadata.json",
    "r",
    encoding="utf-8"
) as f:
    AGREEMENT_METADATA = json.load(f)


# ── FAMILY KEYWORDS ───────────────────────────────────────────────────────
# Used ONLY for family-level routing.
# Do NOT add individual agreement aliases here.

FAMILY_KEYWORDS = {
    "BSNL": [
        "bsnl",
        "bharat sanchar nigam",
    ],
    "AIRTEL": [
        "airtel",
        "bharti airtel",
    ],
    "VODA": [
        "voda",
        "vodafone",
    ],
}


# ── DIRECT PDF KEYWORDS ───────────────────────────────────────────────────
# Agreement-specific identifiers ONLY.
# These uniquely identify ONE agreement and bypass family routing entirely.
# Longer phrases matched before shorter ones (sorted by length desc).

DIRECT_PDF_KEYWORDS = {

    # ── BSNL Voda ────────────────────────────────────────────────────────
    "bsnl voda":                "BSNL & Voda (IP)  MSA dated 20 Jan 2014- USO.pdf",
    "bsnl vodafone":            "BSNL & Voda (IP)  MSA dated 20 Jan 2014- USO.pdf",
    "voda bsnl":                "BSNL & Voda (IP)  MSA dated 20 Jan 2014- USO.pdf",
    "vodafone bsnl":            "BSNL & Voda (IP)  MSA dated 20 Jan 2014- USO.pdf",
    "uso towers":               "BSNL & Voda (IP)  MSA dated 20 Jan 2014- USO.pdf",
    "uso tower":                "BSNL & Voda (IP)  MSA dated 20 Jan 2014- USO.pdf",
    "uso":                      "BSNL & Voda (IP)  MSA dated 20 Jan 2014- USO.pdf",
    "vodafone south":           "BSNL & Voda (IP)  MSA dated 20 Jan 2014- USO.pdf",
    "vodafone cellular":        "BSNL & Voda (IP)  MSA dated 20 Jan 2014- USO.pdf",

    # ── BSNL Idea ────────────────────────────────────────────────────────
    "bsnl idea":                "1. BSNL MSA dated 9 Oct 2015.pdf",
    "idea bsnl":                "1. BSNL MSA dated 9 Oct 2015.pdf",
    "idea cellular infrastructure services limited": "1. BSNL MSA dated 9 Oct 2015.pdf",
    "idea cellular infrastructure": "1. BSNL MSA dated 9 Oct 2015.pdf",
    "idea cellular limited":    "1. BSNL MSA dated 9 Oct 2015.pdf",
    "idea cellular":            "1. BSNL MSA dated 9 Oct 2015.pdf",
    "icisl":                    "1. BSNL MSA dated 9 Oct 2015.pdf",
    "idea":                     "1. BSNL MSA dated 9 Oct 2015.pdf",

    # ── KEC BSNL ─────────────────────────────────────────────────────────
    "kec international limited":"ATC - BSNL KEC AGREEMENT.pdf",
    "kec international":        "ATC - BSNL KEC AGREEMENT.pdf",
    "atc - bsnl":               "ATC - BSNL KEC AGREEMENT.pdf",
    "atc-bsnl":                 "ATC - BSNL KEC AGREEMENT.pdf",
    "atc bsnl":                 "ATC - BSNL KEC AGREEMENT.pdf",
    "bsnl atc":                 "ATC - BSNL KEC AGREEMENT.pdf",
    "bsnl kec":                 "ATC - BSNL KEC AGREEMENT.pdf",
    "kec bsnl":                 "ATC - BSNL KEC AGREEMENT.pdf",
    "kec":                      "ATC - BSNL KEC AGREEMENT.pdf",

    # ── WTTIL BSNL ───────────────────────────────────────────────────────
    "wireless tt info services limited": "WTTIL-BSNL- 3rd EOI MSA(19th April-10).pdf",
    "wireless tt info services":"WTTIL-BSNL- 3rd EOI MSA(19th April-10).pdf",
    "wireless tt":              "WTTIL-BSNL- 3rd EOI MSA(19th April-10).pdf",
    "wttil bsnl":               "WTTIL-BSNL- 3rd EOI MSA(19th April-10).pdf",
    "bsnl wttil":               "WTTIL-BSNL- 3rd EOI MSA(19th April-10).pdf",
    "3rd eoi":                  "WTTIL-BSNL- 3rd EOI MSA(19th April-10).pdf",
    "wttil":                    "WTTIL-BSNL- 3rd EOI MSA(19th April-10).pdf",

    # ── Quippo Airtel ────────────────────────────────────────────────────
    "quippo telecom infrastructure limited": "MSAQuippo-Airtel-29.11.2006.pdf",
    "quippo telecom infrastructure": "MSAQuippo-Airtel-29.11.2006.pdf",
    "quippo telecom":           "MSAQuippo-Airtel-29.11.2006.pdf",
    "quippo airtel":            "MSAQuippo-Airtel-29.11.2006.pdf",
    "airtel quippo":            "MSAQuippo-Airtel-29.11.2006.pdf",
    "quippo":                   "MSAQuippo-Airtel-29.11.2006.pdf",

    # ── Airtel TTIPL ─────────────────────────────────────────────────────
    "telecom tower and infrastructure private limited": "Airtel-TTIPL-masterservicesagmt.PDF",
    "telecom tower and infrastructure": "Airtel-TTIPL-masterservicesagmt.PDF",
    "airtel ttipl":             "Airtel-TTIPL-masterservicesagmt.PDF",
    "ttipl airtel":             "Airtel-TTIPL-masterservicesagmt.PDF",
    "essar":                    "Airtel-TTIPL-masterservicesagmt.PDF",
    "ttipl":                    "Airtel-TTIPL-masterservicesagmt.PDF",

    # ── Topaz (Vodafone & ATC Telecom) ───────────────────────────────────
    "atc telecom infrastructure private limited": "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "atc telecom infrastructure":"Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "atc telecom":              "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "vodafone mobile services limited": "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "vodafone mobile services": "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "vodafone mobile":          "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "atc voda":                 "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "atc vodafone":             "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "voda atc":                 "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "vodafone atc":             "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "atctipl":                  "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "topaz":                    "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",
    "vmsl":                     "Topaz MSA Voda-ATCTIPL MSA for Aquired & New Sites.pdf",

    # ── Bharti Airtel ATC ────────────────────────────────────────────────
    "atc india tower corporation private limited": "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "atc india tower corporation": "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "atc india tower":          "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "atc india":                "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "bharti hexacom limited":   "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "bharti hexacom":           "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "bharti airtel msa":        "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "airtel atc":               "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "atc airtel":               "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "airtel and atc":           "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "airtel hexacom":           "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
    "airtel2":                  "Bharti Airtel MSA - 14th Oct 09 (Comp Ver).pdf",
}

# Keep COMPANY_PATTERNS for backward compat with retriever.py
COMPANY_PATTERNS = {
    "BSNL": [
        "bsnl",
        "bharat sanchar nigam",
        "bharat sanchar nigam limited",
        "bharat sanchar",
        "bsnl limited",
        "m/s bsnl",
        "bharat sanchar nigam ltd",
        "m/s bharat sanchar nigam limited"
    ],
    "AIRTEL": [
        "airtel",
        "bharti airtel",
        "bharti airtel limited",
        "airtel limited",
        "m/s airtel",
        "bal"
    ],
    "IDEA": [
        "idea",
        "idea cellular",
        "idea cellular limited",
        "idea infrastructure",
        "idea cellular infrastructure services limited",
        "icl",
        "m/s idea"
    ],
    "VODAFONE": [
        "vodafone",
        "vodafone india",
        "vodafone india limited",
        "vodafone cellular",
        "vodafone cellular limited",
        "vodafone south",
        "vodafone south limited",
        "vi",
        "vodafone idea",
        "voda",
        "vil",
        "vmsl",
        "m/s vodafone"
    ],
    "RELIANCE": [
        "reliance",
        "reliance communications",
        "reliance communications limited",
        "reliance jio",
        "reliance jio infocomm",
        "rjil",
        "ril",
        "m/s reliance"
    ],
    "TTIPL": [
        "ttipl",
        "telecom tower and infrastructure",
        "telecom tower and infrastructure private limited"
    ],
    "ATC": [
        "atc",
        "atc telecom",
        "atc telecom infrastructure",
        "atc india tower",
        "atc india tower corporation"
    ],
    "QUIPPO": [
        "quippo",
        "quippo telecom",
        "quippo telecom infrastructure"
    ],
    "KEC": [
        "kec",
        "kec international",
        "kec international limited"
    ],
    "WTTIL": [
        "wttil",
        "wireless tt",
        "wireless tt info services",
        "wireless tt info services limited"
    ]
}


def normalize_query(query):
    return query.lower()


def detect_agreement_from_metadata(query):

    print("DIRECT KEYWORDS COUNT:", len(DIRECT_PDF_KEYWORDS))
    print("ATC BSNL IN KEYWORDS:", "atc bsnl" in DIRECT_PDF_KEYWORDS)

    query_lower = normalize_query(query)

    # ── STEP 1: Direct keyword match ─────────────────────────────────────
    sorted_keywords = sorted(
        DIRECT_PDF_KEYWORDS.keys(),
        key=len,
        reverse=True
    )

    for keyword in sorted_keywords:
        if keyword in query_lower:
            matched_pdf = DIRECT_PDF_KEYWORDS[keyword]
            print(f"\nDIRECT KEYWORD MATCH: '{keyword}' → {matched_pdf}")
            return matched_pdf

    # ── STEP 2: Family routing ────────────────────────────────────────────
    for family, keywords in FAMILY_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                # find all agreements in this family
                family_agreements = [
                    a for a in AGREEMENT_METADATA
                    if a.get("family") == family
                ]
                if len(family_agreements) == 1:
                    print(f"\nFAMILY MATCH ({family}) → single agreement")
                    return family_agreements[0]["pdf_name"]
                elif len(family_agreements) > 1:
                    # return None — ambiguity handled in api.py
                    print(f"\nFAMILY MATCH ({family}) → multiple agreements")
                    return None
                break

    return None


def detect_agreement(query, collection=None):
    return detect_agreement_from_metadata(query)