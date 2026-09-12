# -*- coding: utf-8 -*-
"""BISU computing-research Crossref harvester.

September 2026 revision.

The original affiliation-only search missed some valid BISU publications,
especially Springer book chapters whose Crossref author records do not always
carry BISU affiliation strings. This version uses a conservative multi-pass
strategy while keeping Crossref as the metadata source:

1. Affiliation discovery (institution/campus queries).
2. Author expansion from authors whose own Crossref affiliation contains BISU.
3. Trusted-author searches for known BISU computing faculty.
4. Direct DOI checks for verified BISU works previously missed by affiliation search.
5. DOI/title deduplication and explicit evidence fields for auditability.

Author-only hits are accepted only when a trusted BISU author matches and the
work also has a strong computing signal. Such rows are flagged for manual review
when Crossref does not expose a BISU affiliation for that work.
"""

from __future__ import annotations

import csv
import html
import re
import time
import unicodedata
from collections import OrderedDict
from datetime import date
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

CROSSREF_URL = "https://api.crossref.org/works"
MAILTO = "perinmaxangelo@gmail.com"
START_YEAR = 2018
END_YEAR = date.today().year
OUTPUT_CSV = "bisu_computing_crossref_results.csv"
ROWS_PER_REQUEST = 500
AFFILIATION_PAGES = 5
AUTHOR_ROWS = 100
AUTHOR_PAGES = 2
MAX_DYNAMIC_AUTHOR_SEEDS = 150
REQUEST_DELAY_SECONDS = 0.15

ALLOWED_TYPES = {
    "journal-article", "proceedings-article", "book-chapter", "book",
    "monograph", "report", "dissertation", "posted-content", "reference-entry",
}

AFFILIATION_QUERIES = [
    "Bohol Island State University",
    "Bohol Island State University Main Campus",
    "Bohol Island State University Balilihan",
    "Bohol Island State University Bilar",
    "Bohol Island State University Calape",
    "Bohol Island State University Candijay",
    "Bohol Island State University Clarin",
]

TRUSTED_AUTHOR_SEEDS: Dict[str, str] = {
    "Max Angelo Dapitilla Perin": "Bilar Campus",
    "Max Angelo D. Perin": "Bilar Campus",
    "Darrel A. Cardaña": "Bilar Campus",
    "Darrel A. Cardana": "Bilar Campus",
    "Cecilia T. Gumanoy": "Bilar Campus",
    "Cecilia Gumanoy": "Bilar Campus",
    "Joel A. Piollo": "Bilar Campus",
    "Danie D. Baldesco": "Bilar Campus",
    "Rex Vincent D. Tejada": "Bilar Campus",
    "Nelia Q. Catayas": "Bilar Campus",
}

# Verified works that affiliation-only Crossref harvesting previously missed.
# These are direct DOI regression checks, not the only source of additional rows.
KNOWN_DOI_EVIDENCE: Dict[str, Tuple[str, str]] = {
    "10.1007/978-3-032-18846-5_8": ("Darrel A. Cardaña", "Bilar Campus"),
    "10.1007/978-3-032-23515-2_12": ("Darrel A. Cardaña", "Bilar Campus"),
    "10.1007/978-3-032-23515-2_14": ("Max Angelo D. Perin", "Bilar Campus"),
    "10.1007/978-3-032-23716-3_8": ("Max Angelo D. Perin", "Bilar Campus"),
    "10.1007/978-3-032-23716-3_9": ("Max Angelo D. Perin", "Bilar Campus"),
    "10.1007/978-3-032-25187-9_14": ("Darrel A. Cardaña", "Bilar Campus"),
    "10.1007/978-3-032-25187-9_45": ("Cecilia T. Gumanoy", "Bilar Campus"),
    "10.1007/978-3-032-25187-9_46": ("Darrel A. Cardaña", "Bilar Campus"),
}

BISU_ALIAS_MAP: Dict[str, List[str]] = {
    "Main Campus": [
        "bohol island state university main campus",
        "bohol island state university tagbilaran",
        "bisu main campus", "bisu main",
    ],
    "Balilihan Campus": [
        "bohol island state university balilihan campus",
        "bohol island state university balilihan",
        "bisu balilihan campus", "bisu balilihan",
        "college of computing and information sciences bohol island state university balilihan campus",
    ],
    "Bilar Campus": [
        "bohol island state university bilar campus",
        "bohol island state university bilar",
        "bisu bilar campus", "bisu bilar",
        "computer science department college of technology bohol island state university bilar campus",
        "college of technology bohol island state university bilar campus",
    ],
    "Calape Campus": [
        "bohol island state university calape campus",
        "bohol island state university calape",
        "bisu calape campus", "bisu calape",
    ],
    "Candijay Campus": [
        "bohol island state university candijay campus",
        "bohol island state university candijay",
        "bisu candijay campus", "bisu candijay",
    ],
    "Clarin Campus": [
        "bohol island state university clarin campus",
        "bohol island state university clarin",
        "bisu clarin campus", "bisu clarin",
    ],
    "BISU (campus unspecified)": [
        "bohol island state university",
        "bohol island state university bohol philippines",
        "bohol island state university philippines",
        "bisu",
    ],
}

CAMPUS_TOKEN_RULES = {
    "Main Campus": [
        ["bohol", "island", "state", "university", "main"],
        ["bohol", "island", "state", "university", "tagbilaran"],
        ["bisu", "main"],
    ],
    "Balilihan Campus": [["bohol", "island", "state", "university", "balilihan"], ["bisu", "balilihan"]],
    "Bilar Campus": [["bohol", "island", "state", "university", "bilar"], ["bisu", "bilar"]],
    "Calape Campus": [["bohol", "island", "state", "university", "calape"], ["bisu", "calape"]],
    "Candijay Campus": [["bohol", "island", "state", "university", "candijay"], ["bisu", "candijay"]],
    "Clarin Campus": [["bohol", "island", "state", "university", "clarin"], ["bisu", "clarin"]],
}

# Broad college names are intentionally excluded from this list so a generic
# College of Technology/Sciences affiliation cannot by itself make a paper
# computing-related.
COMPUTING_AFFILIATION_HINTS = [
    "department of computer science", "computer science department", "bscs department",
    "department of computer engineering", "computer engineering department",
    "department of information technology", "information technology department",
    "department of information systems", "information systems department",
    "college of computing and information sciences", "school of computing",
    "college of computer studies",
]

COMPUTING_KEYWORDS = [
    "computer science", "computer engineering", "information technology",
    "information system", "information systems", "informatics", "software engineering",
    "software", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "convolutional neural", "long short term memory", "lstm",
    "computer vision", "image processing", "natural language processing",
    "sentiment analysis", "topic modeling", "lda", "vader", "data mining",
    "data science", "big data", "algorithm", "internet of things", "iot", "zigbee",
    "arduino", "raspberry pi", "robotics", "embedded system", "rfid",
    "face recognition", "ocr", "classification", "prediction", "predictive",
    "feature engineering", "logistic regression", "random forest", "support vector",
    "k nearest", "knn", "k-nn", "yolo", "mobilenet", "vgg16", "transfer learning",
    "instance segmentation", "web application", "web based", "web-based",
    "mobile application", "android application", "application programming interface",
    "cloud based", "cloud-based", "cloud computing", "cybersecurity", "network security",
    "data privacy", "database", "information retrieval", "digital transformation",
    "intelligent control", "intelligent system", "automation", "simulation",
    "coppeliasim", "pcb", "optical inspection", "attendance system",
    "detection system", "recognition system", "sign language recognition",
]

PROGRAM_RULES = {
    "Computer Science": [
        "computer science", "machine learning", "deep learning", "neural network",
        "computer vision", "natural language processing", "data mining", "data science",
        "algorithm", "classification", "prediction", "sentiment analysis", "topic modeling",
    ],
    "Computer Engineering": [
        "computer engineering", "embedded system", "robotics", "arduino", "raspberry pi",
        "rfid", "pcb", "zigbee", "intelligent control",
    ],
    "Information Technology": [
        "information technology", "web application", "web based", "web-based",
        "mobile application", "android application", "cloud computing", "cybersecurity",
        "network security", "database",
    ],
    "Information Systems": [
        "information systems", "information system", "digital transformation", "business intelligence",
    ],
}


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=5, connect=5, read=5, backoff_factor=1.2,
        status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": f"{MAILTO} (BISU computing research Crossref harvester)",
        "Accept": "application/json",
    })
    return session


def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(text: Optional[str]) -> str:
    text = clean_text(text).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[-_/(),.;:–—]", " ", text)
    text = re.sub(r"\bphl\b", "philippines", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_person_name(name: str) -> str:
    name = normalize_text(name)
    name = re.sub(r"\b(engr|dr|prof|mr|mrs|ms|mis|mscs|dit|phd)\b", " ", name)
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def person_signature(name: str) -> Tuple[str, str]:
    tokens = normalize_person_name(name).split()
    return (tokens[0], tokens[-1]) if tokens else ("", "")


def same_person(a: str, b: str) -> bool:
    na, nb = normalize_person_name(a), normalize_person_name(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    af, al = person_signature(a)
    bf, bl = person_signature(b)
    return bool(af and al and af == bf and al == bl)


def extract_year(item: dict) -> Optional[int]:
    for key in ("published-print", "published-online", "issued", "created"):
        try:
            return int(item[key]["date-parts"][0][0])
        except Exception:
            continue
    return None


def extract_title(item: dict) -> str:
    title = " ".join(t for t in (item.get("title") or []) if t).strip()
    subtitle = " ".join(t for t in (item.get("subtitle") or []) if t).strip()
    return f"{title}: {subtitle}" if title and subtitle else title or subtitle


def extract_venue(item: dict) -> str:
    if isinstance(item.get("event"), dict):
        event_name = (item.get("event") or {}).get("name") or ""
        if event_name:
            return event_name.strip()
    container = " | ".join(c for c in (item.get("container-title") or []) if c).strip()
    return container or (item.get("publisher") or "").strip() or "Unknown venue"


def extract_author_records(item: dict) -> List[Tuple[str, List[str]]]:
    records: List[Tuple[str, List[str]]] = []
    for author in item.get("author", []) or []:
        literal = (author.get("name") or "").strip()
        given = (author.get("given") or "").strip()
        family = (author.get("family") or "").strip()
        name = literal or f"{given} {family}".strip()
        affs = [
            (aff.get("name") or "").strip()
            for aff in (author.get("affiliation") or [])
            if (aff.get("name") or "").strip()
        ]
        if name:
            records.append((name, affs))
    return records


def extract_authors_and_affiliations(item: dict) -> Tuple[str, List[str]]:
    records = extract_author_records(item)
    authors = ", ".join(name for name, _ in records)
    affiliations: List[str] = []
    for _, affs in records:
        affiliations.extend(affs)
    return authors, affiliations


def match_bisu_campus(affiliations: Sequence[str]) -> Tuple[Optional[str], Optional[str], str]:
    normalized = [(raw, normalize_text(raw)) for raw in affiliations if raw]
    ordered = [
        "Main Campus", "Balilihan Campus", "Bilar Campus", "Calape Campus",
        "Candijay Campus", "Clarin Campus", "BISU (campus unspecified)",
    ]
    for campus in ordered:
        for raw, norm in normalized:
            for alias in BISU_ALIAS_MAP.get(campus, []):
                if normalize_text(alias) in norm:
                    return campus, raw, "high"
    for campus, groups in CAMPUS_TOKEN_RULES.items():
        for raw, norm in normalized:
            for tokens in groups:
                if all(token in norm for token in tokens):
                    return campus, raw, "medium"
    for raw, norm in normalized:
        if "bohol island state university" in norm or re.search(r"\bbisu\b", norm):
            return "BISU (campus unspecified)", raw, "low"
    return None, None, "none"


def bisu_author_evidence(item: dict) -> List[Tuple[str, str]]:
    evidence: List[Tuple[str, str]] = []
    for name, affs in extract_author_records(item):
        campus, _, _ = match_bisu_campus(affs)
        if campus:
            evidence.append((name, campus))
    return evidence


def trusted_author_match(item: dict, trusted: Dict[str, str]) -> Optional[Tuple[str, str]]:
    for item_name, _ in extract_author_records(item):
        for seed_name, campus in trusted.items():
            if same_person(item_name, seed_name):
                return seed_name, campus
    return None


def is_computing_record(item: dict, affiliations: Sequence[str]) -> bool:
    title = extract_title(item)
    subjects = " ".join(item.get("subject") or [])
    container = " ".join(item.get("container-title") or [])
    event_name = ""
    if isinstance(item.get("event"), dict):
        event_name = (item.get("event") or {}).get("name") or ""
    blob = normalize_text(f"{title} {subjects} {container} {event_name}")
    aff_blob = normalize_text(" ".join(affiliations))
    if any(normalize_text(k) in blob for k in COMPUTING_KEYWORDS):
        return True
    if any(normalize_text(h) in aff_blob for h in COMPUTING_AFFILIATION_HINTS):
        return True
    return False


def infer_program(item: dict, affiliations: Sequence[str]) -> str:
    title = extract_title(item)
    subjects = " ".join(item.get("subject") or [])
    container = " ".join(item.get("container-title") or [])
    blob = normalize_text(f"{title} {subjects} {container} {' '.join(affiliations)}")
    scores = {program: 0 for program in PROGRAM_RULES}
    for program, patterns in PROGRAM_RULES.items():
        for pattern in patterns:
            if normalize_text(pattern) in blob:
                scores[program] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] else "Computing (unspecified)"


def dedup_key_from_item(item: dict) -> str:
    doi = (item.get("DOI") or "").strip().lower()
    if doi:
        return f"doi::{doi}"
    return f"title::{normalize_text(extract_title(item))}::{extract_year(item) or 0}"


def merge_discovery(existing: dict, incoming: dict) -> dict:
    if not existing:
        return incoming
    methods = set(existing.get("_discovery_methods", [])) | set(incoming.get("_discovery_methods", []))
    ex_aff = sum(len(a) for _, a in extract_author_records(existing))
    in_aff = sum(len(a) for _, a in extract_author_records(incoming))
    chosen = incoming if in_aff > ex_aff else existing
    chosen["_discovery_methods"] = sorted(methods)
    return chosen


def request_items(session: requests.Session, params: dict) -> List[dict]:
    response = session.get(CROSSREF_URL, params=params, timeout=60)
    if response.status_code != 200:
        print(f"[WARN] Crossref status={response.status_code} params={params}")
        return []
    return (response.json().get("message") or {}).get("items") or []


def fetch_affiliation_candidates(session: requests.Session) -> List[dict]:
    out: List[dict] = []
    for query in AFFILIATION_QUERIES:
        for page in range(AFFILIATION_PAGES):
            offset = page * ROWS_PER_REQUEST
            params = {
                "query.affiliation": query,
                "filter": f"from-pub-date:{START_YEAR}-01-01,until-pub-date:{END_YEAR}-12-31",
                "rows": ROWS_PER_REQUEST,
                "offset": offset,
                "mailto": MAILTO,
            }
            items = request_items(session, params)
            print(f"[AFFILIATION] {query!r} offset={offset}: {len(items)}")
            for item in items:
                item["_discovery_methods"] = [f"affiliation:{query}"]
                out.append(item)
            if len(items) < ROWS_PER_REQUEST:
                break
            time.sleep(REQUEST_DELAY_SECONDS)
    return out


def fetch_author_candidates(session: requests.Session, author_name: str) -> List[dict]:
    out: List[dict] = []
    for page in range(AUTHOR_PAGES):
        offset = page * AUTHOR_ROWS
        params = {
            "query.author": author_name,
            "filter": f"from-pub-date:{START_YEAR}-01-01,until-pub-date:{END_YEAR}-12-31",
            "rows": AUTHOR_ROWS,
            "offset": offset,
            "mailto": MAILTO,
        }
        items = request_items(session, params)
        print(f"[AUTHOR] {author_name!r} offset={offset}: {len(items)}")
        for item in items:
            item["_discovery_methods"] = [f"author:{author_name}"]
            out.append(item)
        if len(items) < AUTHOR_ROWS:
            break
        time.sleep(REQUEST_DELAY_SECONDS)
    return out


def fetch_doi_candidate(session: requests.Session, doi: str) -> Optional[dict]:
    response = session.get(f"{CROSSREF_URL}/{doi}", params={"mailto": MAILTO}, timeout=60)
    if response.status_code != 200:
        print(f"[DOI] {doi}: status={response.status_code}")
        return None
    item = response.json().get("message") or {}
    item["_discovery_methods"] = [f"known-doi:{doi}"]
    print(f"[DOI] {doi}: found {extract_title(item)!r}")
    return item


def learn_trusted_authors(items: Iterable[dict]) -> Dict[str, str]:
    learned: Dict[str, str] = dict(TRUSTED_AUTHOR_SEEDS)
    for item in items:
        for name, campus in bisu_author_evidence(item):
            if name not in learned or learned[name] == "BISU (campus unspecified)":
                learned[name] = campus
    compact: "OrderedDict[Tuple[str, str], Tuple[str, str]]" = OrderedDict()
    for name, campus in learned.items():
        sig = person_signature(name)
        if not all(sig):
            continue
        if sig not in compact or compact[sig][1] == "BISU (campus unspecified)":
            compact[sig] = (name, campus)
    result = {name: campus for name, campus in compact.values()}
    print(f"[AUTHORS] Trusted BISU author seeds: {len(result)}")
    return result


def build_row(item: dict, trusted_authors: Dict[str, str]) -> Optional[dict]:
    year = extract_year(item)
    title = extract_title(item)
    work_type = item.get("type") or ""
    if not year or year < START_YEAR or year > END_YEAR or not title:
        return None
    if ALLOWED_TYPES and work_type not in ALLOWED_TYPES:
        return None

    researchers, affiliations = extract_authors_and_affiliations(item)
    direct_campus, matched_aff, campus_conf = match_bisu_campus(affiliations)
    direct_authors = bisu_author_evidence(item)
    trusted_match = trusted_author_match(item, trusted_authors)
    doi = (item.get("DOI") or "").strip().lower()
    doi_seed = KNOWN_DOI_EVIDENCE.get(doi)

    evidence_author = ""
    validation_evidence = ""
    needs_review = "NO"

    if direct_campus:
        campus = direct_campus
        validation_evidence = "Crossref BISU affiliation"
        if direct_authors:
            evidence_author = "; ".join(name for name, _ in direct_authors)
    elif doi_seed:
        evidence_author, campus = doi_seed
        validation_evidence = "Verified DOI seed (affiliation missing/incomplete in Crossref work metadata)"
    elif trusted_match:
        evidence_author, campus = trusted_match
        validation_evidence = "Trusted BISU author match; Crossref work affiliation missing/incomplete"
        needs_review = "YES"
    else:
        return None

    if not is_computing_record(item, affiliations):
        return None

    discovery_methods = "; ".join(item.get("_discovery_methods", []))
    return {
        "Year": year,
        "CampusMatched": campus,
        "CampusMatchedConfidence": campus_conf if direct_campus else ("verified-doi" if doi_seed else "author-evidence"),
        "ProgramInferred": infer_program(item, affiliations),
        "Title": title,
        "Researchers": researchers,
        "Venue": extract_venue(item),
        "Publisher": item.get("publisher", "") or "",
        "Type": work_type,
        "DOI": item.get("DOI", "") or "",
        "URL": item.get("URL", "") or "",
        "MatchedAffiliation": matched_aff or "",
        "AllAffiliations": " | ".join(affiliations),
        "Subjects": "; ".join(item.get("subject") or []),
        "Abstract": clean_text(item.get("abstract")),
        "CrossrefQueryUsed": discovery_methods,
        "DiscoveryMethod": discovery_methods,
        "BISUAuthorEvidence": evidence_author,
        "ValidationEvidence": validation_evidence,
        "NeedsManualReview": needs_review,
    }


def save_rows(rows: List[dict]) -> None:
    if not rows:
        raise RuntimeError("No validated BISU computing records found; refusing to overwrite the CSV.")
    fieldnames = [
        "Year", "CampusMatched", "CampusMatchedConfidence", "ProgramInferred", "Title",
        "Researchers", "Venue", "Publisher", "Type", "DOI", "URL", "MatchedAffiliation",
        "AllAffiliations", "Subjects", "Abstract", "CrossrefQueryUsed", "DiscoveryMethod",
        "BISUAuthorEvidence", "ValidationEvidence", "NeedsManualReview",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[DONE] Saved {len(rows)} rows to {OUTPUT_CSV}")


def main() -> None:
    session = build_session()

    # Pass 1: institution/campus search.
    affiliation_items = fetch_affiliation_candidates(session)

    # Learn BISU authors only when that author's own Crossref affiliation is BISU.
    # Then search those authors directly to recover records with missing affiliations.
    trusted_authors = learn_trusted_authors(affiliation_items)
    dynamic_author_names = list(trusted_authors.keys())[:MAX_DYNAMIC_AUTHOR_SEEDS]

    candidates: Dict[str, dict] = {}
    for item in affiliation_items:
        key = dedup_key_from_item(item)
        candidates[key] = merge_discovery(candidates.get(key, {}), item)

    for author_name in dynamic_author_names:
        for item in fetch_author_candidates(session, author_name):
            key = dedup_key_from_item(item)
            candidates[key] = merge_discovery(candidates.get(key, {}), item)

    # Direct DOI regression checks guarantee known missing Springer chapters stay included.
    for doi in KNOWN_DOI_EVIDENCE:
        item = fetch_doi_candidate(session, doi)
        if item:
            key = dedup_key_from_item(item)
            candidates[key] = merge_discovery(candidates.get(key, {}), item)

    rows: List[dict] = []
    for item in candidates.values():
        row = build_row(item, trusted_authors)
        if row:
            rows.append(row)

    rows.sort(
        key=lambda r: (int(r["Year"]), r["CampusMatched"], r["ProgramInferred"], r["Title"].lower()),
        reverse=True,
    )
    save_rows(rows)

    print("\n[SUMMARY]")
    print(f"Candidate works after DOI/title deduplication: {len(candidates)}")
    print(f"Validated BISU computing records: {len(rows)}")
    print(f"Author-evidence records needing review: {sum(r['NeedsManualReview'] == 'YES' for r in rows)}")
    print(f"Springer records: {sum('springer' in normalize_text(r['Publisher']) for r in rows)}")
    print(f"Bilar records: {sum(r['CampusMatched'] == 'Bilar Campus' for r in rows)}")

    print("\n[KNOWN DOI REGRESSION CHECK]")
    found_dois = {(r.get("DOI") or "").lower() for r in rows}
    missing = [doi for doi in KNOWN_DOI_EVIDENCE if doi.lower() not in found_dois]
    if missing:
        for doi in missing:
            print(f"  MISSING: {doi}")
        raise RuntimeError(f"Known verified BISU DOI regression failure: {len(missing)} missing")
    print(f"  PASS: all {len(KNOWN_DOI_EVIDENCE)} known verified DOI seeds are present")


if __name__ == "__main__":
    main()
