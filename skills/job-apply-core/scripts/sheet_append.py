#!/usr/bin/env python3
"""Append ONE application row to the tracker sheet. The only supported way.

Why a helper: a hand-rolled append with a miscounted field list shifts every column left (this
hit five rows once), and Sheets USER_ENTERED turns text like "+880 17.." or "=..." into formulas.
This helper enforces the column contract, checks the live header width, and writes RAW text.

Two modes:
  kit sheet (default)   exactly 15 columns A..O (see references/tracker-columns.md).
  adopted sheet         the user gave their own sheet: sheet_init --adopt matched its headers
                        (any order, extras ignored) and saved them to config sheet_columns.
                        Appends place values at the matched positions and abort when the
                        live header drifts from the saved one.

Usage:
  python3 sheet_append.py append '<json-row>' [--dry-run]
Row JSON: an object with these keys (missing keys become empty), or an array of exactly 15 values
(arrays need the fixed kit order and are rejected for adopted sheets):
  date, company, position, drive_link, job_nature, job_type, location, job_link, job_desc,
  status, how_applied, contact, salary, deadline, comments
Column I = full job description text; column O = extra info only (ids, notes), never JD text.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

COLUMNS = ["date", "company", "position", "drive_link", "job_nature", "job_type", "location",
           "job_link", "job_desc", "status", "how_applied", "contact", "salary", "deadline", "comments"]
HEADERS = ["Date", "Company", "Position", "Resume Drive", "Job Nature", "Job Type", "Location",
           "Job Link", "Job Description", "Job Status", "How Applied", "Contact/Email",
           "Salary/Budget", "Deadline", "Comments"]
assert len(COLUMNS) == len(HEADERS) == 15

# Normalized-header aliases for adopting a user's own sheet (see sheet_init --adopt).
ALIASES = {
    "date": ["date"],
    "company": ["company", "employer", "organization"],
    "position": ["position", "title", "role", "jobtitle", "job"],
    "drive_link": ["resumedrive", "drive", "drivelink", "resume", "resumelink", "cv", "cvlink", "document"],
    "job_nature": ["jobnature", "nature", "employmenttype", "employment"],
    "job_type": ["jobtype", "type", "workplace", "workmode", "workplacetype"],
    "location": ["location", "city", "place"],
    "job_link": ["joblink", "link", "url", "post", "posting", "postingurl", "postlink", "applylink", "joburl"],
    "job_desc": ["jobdescription", "description", "jd", "details", "jobdetails"],
    "status": ["jobstatus", "status", "state", "stage"],
    "how_applied": ["howapplied", "appliedvia", "method", "applymethod", "channel"],
    "contact": ["contactemail", "contact", "email", "recruiter", "hr", "contactperson"],
    "salary": ["salarybudget", "salary", "budget", "pay", "compensation"],
    "deadline": ["deadline", "duedate", "closingdate", "lastdate", "applyby"],
    "comments": ["comments", "comment", "notes", "note", "remarks", "extra", "info"],
}


class RowError(ValueError):
    pass


def _norm(h) -> str:
    return re.sub(r"[^a-z0-9]", "", str(h or "").lower())


def column_map_from_header(header: list) -> dict[str, int]:
    """Match a live header row to the 15 keys. Returns {key: 0-based index}.

    Standard headers match first; the rest match ALIASES. Extra columns are
    ignored. Raises RowError naming missing or ambiguous columns.
    """
    normed = [_norm(h) for h in header]
    known = {_norm(h): k for h, k in zip(HEADERS, COLUMNS)}
    mapping: dict[str, int] = {}
    used: set[int] = set()
    for i, n in enumerate(normed):
        if n and n in known and known[n] not in mapping:
            mapping[known[n]] = i
            used.add(i)
    ambiguous: list[str] = []
    for key in COLUMNS:
        if key in mapping:
            continue
        cands = [i for i, n in enumerate(normed) if i not in used and n in ALIASES[key]]
        if len(cands) == 1:
            mapping[key] = cands[0]
            used.add(cands[0])
        elif len(cands) > 1:
            ambiguous.append(f"{key} (columns {[header[i] for i in cands]})")
    # A leftover column that ALSO means an already-mapped key is ambiguous too
    # (e.g. "Job Status" plus "State"): the agent must ask which one to use.
    for i, n in enumerate(normed):
        if i in used or not n:
            continue
        for key in COLUMNS:
            if key in mapping and n in ALIASES[key]:
                ambiguous.append(f"{key} (columns {[header[mapping[key]], header[i]]})")
                break
    missing = [k for k in COLUMNS if k not in mapping]
    problems = [f"missing: {missing}"] * bool(missing) + [f"ambiguous: {ambiguous}"] * bool(ambiguous)
    if problems:
        raise RowError("header does not cover the 15 tracked columns — " + "; ".join(problems)
                       + f". Live header: {list(header)}")
    return mapping


def col_letter(n: int) -> str:
    """1-based column number -> A1 letter(s)."""
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def sheet_id_from_url(url: str) -> str | None:
    """Extract a spreadsheet id from a full Google Sheets URL (None when not one)."""
    m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", url or "")
    return m.group(1) if m else None


def resolve_sheet_id(cfg) -> str | None:
    """Config sheet_id, else the id parsed from config sheet_url (paste-the-URL field)."""
    sid = (cfg.get("sheet_id") or "").strip()
    if sid:
        return sid
    return sheet_id_from_url(cfg.get("sheet_url") or "")


def build_row(obj) -> list[str]:
    if isinstance(obj, list):
        if len(obj) != 15:
            raise RowError(f"row has {len(obj)} values, expected 15 (A=Date .. O=Comments)")
        vals = obj
    elif isinstance(obj, dict):
        unknown = sorted(set(obj) - set(COLUMNS))
        if unknown:
            raise RowError(f"unknown keys {unknown}; allowed: {COLUMNS}")
        vals = [obj.get(k, "") for k in COLUMNS]
    else:
        raise RowError("row must be a JSON object or array")
    return ["" if v is None else str(v) for v in vals]


def build_mapped_row(obj: dict, mapping: dict[str, int], width: int) -> list[str]:
    """Place dict values at mapped positions; every other cell stays blank."""
    if not isinstance(obj, dict):
        raise RowError("mapped append needs a JSON object (arrays need fixed 15-column order)")
    unknown = sorted(set(obj) - set(COLUMNS))
    if unknown:
        raise RowError(f"unknown keys {unknown}; allowed: {COLUMNS}")
    vals = [""] * width
    for k, v in obj.items():
        vals[mapping[k]] = "" if v is None else str(v)
    return vals


def saved_columns(cfg) -> list | None:
    """Header texts adopted via sheet_init --adopt (None = legacy exact-15 sheet)."""
    raw = cfg.get("sheet_columns")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        raise RowError("config sheet_columns is not valid JSON (re-run sheet_init --adopt)")
    return data if isinstance(data, list) else None


def resolve_mapping(header: list, cfg) -> tuple[dict[str, int] | None, int]:
    """Returns (mapping, width). mapping None = legacy fixed A..O order."""
    saved = saved_columns(cfg)
    if saved is None:
        return None, 15
    if [_norm(h) for h in header] != [_norm(h) for h in saved]:
        raise RowError("live header no longer matches the adopted sheet_columns "
                       f"(live: {list(header)}). Re-run sheet_init --adopt, or fix the sheet by hand.")
    return column_map_from_header(header), len(header)


def append(obj, sheet_id: str | None = None, tab: str | None = None, dry_run: bool = False, **kw) -> dict:
    import jak_google as google
    import jak_config
    cfg = jak_config.load()
    sheet_id = sheet_id or resolve_sheet_id(cfg) or ("<sheet_id not set>" if dry_run else None)
    if not sheet_id:
        raise RowError("no tracker sheet configured (paste its URL into config sheet_url, or run sheet_init --adopt)")
    tab = tab or cfg.get("sheet_tab") or "Sheet1"
    saved = saved_columns(cfg)
    if dry_run:
        if saved is None:
            row = build_row(obj)
            return {"dry_run": True, "sheet_id": sheet_id, "range": f"{tab}!A:O", "values": [row]}
        mapping = column_map_from_header(saved)
        row = build_mapped_row(obj, mapping, len(saved))
        return {"dry_run": True, "sheet_id": sheet_id,
                "range": f"{tab}!A:{col_letter(len(saved))}", "values": [row]}
    header = google.sheet_get(sheet_id, f"{tab}!A1:Z1", **kw)
    header = header[0] if header else []
    if saved is None:
        if len(header) != 15:
            raise RowError(f"live header row has {len(header)} columns, expected 15 (run sheet_init for a new sheet). Header: {header}")
        res = google.sheet_append(sheet_id, f"{tab}!A:O", [build_row(obj)], **kw)
        res["row_cells"] = 15
        return res
    mapping, width = resolve_mapping(header, cfg)
    rng = f"{tab}!A:{col_letter(width)}"
    res = google.sheet_append(sheet_id, rng, [build_mapped_row(obj, mapping, width)], **kw)
    res["row_cells"] = width
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("append")
    p.add_argument("row_json")
    p.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        out = append(json.loads(a.row_json), dry_run=a.dry_run)
    except (RowError, json.JSONDecodeError) as e:
        print(f"ABORT: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print("APPENDED " + out.get("range", "") if not out.get("dry_run") else json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
