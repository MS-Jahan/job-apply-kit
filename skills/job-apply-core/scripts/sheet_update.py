#!/usr/bin/env python3
"""Update cells of an EXISTING tracker row (the find → add → update flow).

Appending is for new jobs (sheet_append.py). This helper is for what happens
after: the draft id lands in comments, the status moves Found → Drafted →
Staged → Applied. Statuses outside that pipeline (the user hand-setting
"sent", "on hold", ...) are never overwritten without --force.

Usage:
  python3 sheet_update.py find --company ACME --position "Backend Dev" [--job-link URL] [--tab T]
      prints matching row numbers with their current status (match on company +
      position; --job-link narrows it further).
  python3 sheet_update.py set ROW '<json-partial>' [--tab T] [--dry-run] [--force]
      writes only the given keys (e.g. '{"status":"Drafted","comments":"draft r_123"}')
      to their mapped columns, RAW. One single-cell API call per key.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Status values the agent itself writes, in pipeline order. Anything else in
# the status cell is treated as hand-set by the user and needs --force.
PIPELINE = ["", "Found", "Drafted", "Staged", "Applied"]


class UpdateError(ValueError):
    pass


def _ctx(tab: str | None):
    import jak_config
    import sheet_append as sa
    cfg = jak_config.load()
    sheet_id = sa.resolve_sheet_id(cfg)
    if not sheet_id:
        raise UpdateError("no tracker sheet configured (paste its URL into config sheet_url, or run sheet_init --adopt)")
    tab = tab or cfg.get("sheet_tab") or "Sheet1"
    return cfg, sa, sheet_id, tab


def find(company: str, position: str, job_link: str = "", tab: str | None = None, limit: int = 1000) -> list[dict]:
    """Scan company/position columns (+ optional job-link) for matching rows."""
    import jak_google as google
    cfg, sa, sheet_id, tab = _ctx(tab)
    saved = sa.saved_columns(cfg)
    header = google.sheet_get(sheet_id, f"{tab}!A1:Z1")
    header = header[0] if header else []
    if saved is None:
        if len(header) != 15:
            raise UpdateError(f"live header has {len(header)} columns, expected 15")
        mapping = {k: i for i, k in enumerate(sa.COLUMNS)}
    else:
        mapping, _ = sa.resolve_mapping(header, cfg)
    cols = google.sheet_get(sheet_id, f"{tab}!A2:Z{limit + 1}")
    want_c, want_p = company.strip().lower(), position.strip().lower()
    hits = []
    for n, row in enumerate(cols, start=2):
        def cell(key):
            i = mapping[key]
            return row[i].strip() if i < len(row) else ""
        if cell("company").lower() == want_c and cell("position").lower() == want_p:
            if job_link and cell("job_link") != job_link.strip():
                continue
            hits.append({"row": n, "company": cell("company"), "position": cell("position"),
                         "status": cell("status"), "job_link": cell("job_link"),
                         "comments": cell("comments")})
    return hits


def set_cells(row: int, partial: dict, tab: str | None = None, dry_run: bool = False,
              force: bool = False, **kw) -> dict:
    """Write partial {key: value} to mapped cells of ROW. Returns what was written."""
    import jak_google as google
    cfg, sa, sheet_id, tab = _ctx(tab)
    if row < 2:
        raise UpdateError("row must be >= 2 (row 1 is the header)")
    if not isinstance(partial, dict) or not partial:
        raise UpdateError("partial must be a non-empty JSON object")
    unknown = sorted(set(partial) - set(sa.COLUMNS))
    if unknown:
        raise UpdateError(f"unknown keys {unknown}; allowed: {sa.COLUMNS}")
    saved = sa.saved_columns(cfg)
    header = google.sheet_get(sheet_id, f"{tab}!A1:Z1", **kw)
    header = header[0] if header else []
    if saved is None:
        if len(header) != 15:
            raise UpdateError(f"live header has {len(header)} columns, expected 15")
        mapping = {k: i for i, k in enumerate(sa.COLUMNS)}
    else:
        mapping, _ = sa.resolve_mapping(header, cfg)
    current = google.sheet_get(sheet_id, f"{tab}!A{row}:Z{row}", **kw)
    current = current[0] if current else []
    if "status" in partial:
        cur = current[mapping["status"]].strip() if mapping["status"] < len(current) else ""
        new = str(partial["status"])
        if cur != new and cur not in PIPELINE and not force:
            raise UpdateError(
                f"status cell holds {cur!r} (looks hand-set by the user) — refusing to overwrite "
                f"with {new!r}. Re-check with the user, or pass --force.")
    writes = []
    for key, val in partial.items():
        cell = f"{tab}!{sa.col_letter(mapping[key] + 1)}{row}"
        writes.append({"key": key, "range": cell, "value": "" if val is None else str(val)})
    if dry_run:
        return {"dry_run": True, "sheet_id": sheet_id, "writes": writes}
    for w in writes:
        google.sheet_update(sheet_id, w["range"], [[w["value"]]], **kw)
    return {"row": row, "writes": writes}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("find")
    p.add_argument("--company", required=True)
    p.add_argument("--position", required=True)
    p.add_argument("--job-link", default="")
    p.add_argument("--tab")
    p = sub.add_parser("set")
    p.add_argument("row", type=int)
    p.add_argument("partial_json")
    p.add_argument("--tab")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "find":
            hits = find(a.company, a.position, a.job_link, a.tab)
            if not hits:
                print("no matching rows")
            for h in hits:
                print(f"row {h['row']}: {h['company']} | {h['position']} | status={h['status']!r}")
            return 0
        out = set_cells(a.row, json.loads(a.partial_json), a.tab, a.dry_run, a.force)
    except (UpdateError, json.JSONDecodeError) as e:
        print(f"ABORT: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
