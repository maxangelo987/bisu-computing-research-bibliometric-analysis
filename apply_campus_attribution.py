# -*- coding: utf-8 -*-
"""Resolve BISU campus attribution after Crossref harvesting.

Campus attribution uses two evidence sources:
1) explicit campus names in Crossref affiliation metadata; and
2) a small, auditable author-to-campus map confirmed by the project author.

A publication may contribute to more than one campus.  In that case every
contributing BISU campus receives one full publication credit in campus-level
analysis, while the publication itself remains a single unique record in the
bibliometric dataset.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

CSV_PATH = Path("bisu_computing_crossref_results.csv")

CAMPUS_ORDER = [
    "Main Campus",
    "Balilihan Campus",
    "Bilar Campus",
    "Calape Campus",
    "Candijay Campus",
    "Clarin Campus",
]

# Confirmed campus affiliations supplied by the study author on 2026-09-12.
# Variants are intentionally explicit and auditable.
AUTHOR_CAMPUS = {
    "max angelo dapitilla perin": "Bilar Campus",
    "max angelo d perin": "Bilar Campus",
    "max angelo perin": "Bilar Campus",
    "darrel a cardana": "Bilar Campus",
    "darrel abuyabor cardana": "Bilar Campus",
    "darrel cardana": "Bilar Campus",
    "cecilia t gumanoy": "Bilar Campus",
    "cecilia gumanoy": "Bilar Campus",
    "epifelward nino o amora": "Candijay Campus",
    "epifelward nino olaivar amora": "Candijay Campus",
    "epifelward nino amora": "Candijay Campus",
    "julius c castro": "Main Campus",
    "deanne cameren p evangelista": "Main Campus",
    "deanne cameren evangelista": "Main Campus",
    "myriam j polinar": "Main Campus",
    "myriam c jumila polinar": "Main Campus",
    "roselle p cimagala": "Main Campus",
    "edgar e uy": "Main Campus",
}

# High-confidence mappings already supported by explicit BISU campus metadata in
# the harvested corpus.  These help resolve works whose individual Crossref work
# record contains only a generic BISU affiliation.
EVIDENCE_BACKED_AUTHOR_CAMPUS = {
    "alvin t remolado": "Clarin Campus",
    "jeralyn alagon": "Main Campus",
    "elaine m cepe": "Main Campus",
}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def explicit_campuses(text: str) -> set[str]:
    t = norm(text)
    found: set[str] = set()
    rules = {
        "Main Campus": ["main campus", "tagbilaran"],
        "Balilihan Campus": ["balilihan campus", "bisu balilihan", "state university balilihan"],
        "Bilar Campus": ["bilar campus", "bisu bilar", "state university bilar"],
        "Calape Campus": ["calape campus", "bisu calape", "state university calape"],
        "Candijay Campus": ["candijay campus", "bisu candijay", "state university candijay"],
        "Clarin Campus": ["clarin campus", "bisu clarin", "state university clarin", "clarin poblacion norte"],
    }
    for campus, phrases in rules.items():
        if any(norm(p) in t for p in phrases):
            found.add(campus)
    return found


def author_campuses(researchers: str) -> set[str]:
    text = norm(researchers)
    found: set[str] = set()
    mapping = dict(EVIDENCE_BACKED_AUTHOR_CAMPUS)
    mapping.update(AUTHOR_CAMPUS)
    for author, campus in mapping.items():
        if norm(author) in text:
            found.add(campus)
    return found


def ordered(campuses: set[str]) -> list[str]:
    return [c for c in CAMPUS_ORDER if c in campuses]


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        old_fields = list(rows[0].keys()) if rows else []

    if not rows:
        raise SystemExit("Dataset is empty")

    changed = 0
    multi = 0
    still_unspecified = 0

    for row in rows:
        campuses = set()
        campuses |= explicit_campuses(row.get("AllAffiliations", ""))
        campuses |= explicit_campuses(row.get("MatchedAffiliation", ""))
        campuses |= author_campuses(row.get("Researchers", ""))

        current = row.get("CampusMatched", "")
        if current in CAMPUS_ORDER:
            campuses.add(current)

        resolved = ordered(campuses)
        row["ContributingCampuses"] = " | ".join(resolved)
        row["CampusAttributionMethod"] = (
            "full-counting: explicit affiliation and/or confirmed author-campus mapping"
            if resolved else "unresolved"
        )

        if len(resolved) == 1:
            new_primary = resolved[0]
        elif len(resolved) > 1:
            new_primary = "Multiple BISU campuses"
            multi += 1
        else:
            new_primary = current or "BISU (campus unspecified)"
            if new_primary == "BISU (campus unspecified)":
                still_unspecified += 1

        if new_primary != current:
            changed += 1
        row["CampusMatched"] = new_primary

    fields = list(old_fields)
    for extra in ("ContributingCampuses", "CampusAttributionMethod"):
        if extra not in fields:
            fields.append(extra)

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Campus attribution updated for {changed} records")
    print(f"Multi-campus collaborations: {multi}")
    print(f"Still campus-unspecified: {still_unspecified}")
    for campus in CAMPUS_ORDER:
        count = sum(campus in (r.get("ContributingCampuses") or "").split(" | ") for r in rows)
        print(f"FULL_COUNT {campus}: {count}")


if __name__ == "__main__":
    main()
