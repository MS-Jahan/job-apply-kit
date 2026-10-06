#!/usr/bin/env python3
"""Append ONE application row to the tracker sheet (15 columns A..O). The only supported way.

Why a helper: a hand-rolled append with a miscounted field list shifts every column left (this
hit five rows once), and Sheets USER_ENTERED turns text like "+880 17.." or "=..." into formulas.
This helper enforces the column contract, checks the live header width, and writes RAW text.

Usage:
  python3 sheet_append.py append '<json-row>' [--dry-run]
Row JSON: an object with these keys (missing keys become empty), or an array of exactly 15 values:
  date, company, position, drive_link, job_nature, job_type, location, job_link, job_desc,
  status, how_applied, contact, salary, deadline, comments
Column I = full job description text; column O = extra info only (ids, notes), never JD text.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

COLUMNS = ["date", "company", "position", "drive_link", "job_nature", "job_type", "location",
           "job_link", "job_desc", "status", "how_applied", "contact", "salary", "deadline", "comments"]
HEADERS = ["Date", "Company", "Position", "Resume Drive", "Job Nature", "Job Type", "Location",
           "Job Link", "Job Description", "Job Status", "How Applied", "Contact/Email",
           "Salary/Budget", "Deadline", "Comments"]
assert len(COLUMNS) == len(HEADERS) == 15


class RowError(ValueError):
    pass


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


def append(obj, sheet_id: str | None = None, tab: str | None = None, dry_run: bool = False, **kw) -> dict:
    import jak_google as google
    import jak_config
    row = build_row(obj)
    cfg = jak_config.load()
    sheet_id = sheet_id or (cfg.get("sheet_id") or "<sheet_id not set>" if dry_run else cfg.require("sheet_id"))
    tab = tab or cfg.get("sheet_tab") or "Sheet1"
    if dry_run:
        return {"dry_run": True, "sheet_id": sheet_id, "range": f"{tab}!A:O", "values": [row]}
    header = google.sheet_get(sheet_id, f"{tab}!A1:O1", **kw)
    width = len(header[0]) if header else 0
    if width != 15:
        raise RowError(f"live header row has {width} columns, expected 15 (run sheet_init for a new sheet). Header: {header}")
    res = google.sheet_append(sheet_id, f"{tab}!A:O", [row], **kw)
    res["row_cells"] = 15
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
