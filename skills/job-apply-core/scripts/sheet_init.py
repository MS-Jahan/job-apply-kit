#!/usr/bin/env python3
"""One-time setup for a new user: create the Drive folder, a `templates` subfolder and the tracker
sheet (with the 15 headers A..O), then write the ids into config.md. Existing ids are kept.

Usage: python3 sheet_init.py [--dry-run]
       python3 sheet_init.py --adopt SHEET_ID_OR_URL [--tab NAME] [--dry-run]
--adopt keeps the user's OWN sheet: its header row is matched to the 15 tracked columns
(any order; extra columns are ignored and never written) and the match is saved to config
sheet_columns. Appends/updates then place values at the matched positions and abort when
the live header drifts. Needs a usable Google backend (see doctor.sh). Nothing is shared
publicly here; resume files are shared one by one at upload time, and only inside this folder.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jak_google as google  # noqa: E402
import jak_config  # noqa: E402
from sheet_append import HEADERS, column_map_from_header  # noqa: E402


def sheet_id_from(s: str) -> str:
    m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", s)
    return m.group(1) if m else s.strip()


def adopt(sheet_ref: str, tab: str | None, dry_run: bool) -> int:
    cfg = jak_config.load()
    sheet_id = sheet_id_from(sheet_ref)
    tab = tab or cfg.get("sheet_tab") or "Sheet1"
    header = google.sheet_get(sheet_id, f"{tab}!A1:Z1")
    header = [c for c in (header[0] if header else []) if str(c).strip()]
    if not header:
        print(f"ABORT: no header row found in {tab}!A1:Z1", file=sys.stderr)
        return 1
    try:
        mapping = column_map_from_header(header)
    except Exception as e:  # noqa: BLE001
        print(f"ABORT: {e}", file=sys.stderr)
        print("Fix the sheet headers by hand, or ask the user which column means what.", file=sys.stderr)
        return 1
    print(f"adopted sheet {sheet_id} tab {tab}: matched all 15 tracked columns")
    for k in sorted(mapping, key=mapping.get):
        print(f"  col {mapping[k] + 1:>2}  {header[mapping[k]]!r:28} -> {k}")
    extra = [h for i, h in enumerate(header) if i not in set(mapping.values())]
    if extra:
        print(f"ignored extra columns (never written): {extra}")
    if dry_run:
        return 0
    jak_config.update_keys(jak_config.config_path(),
                           {"sheet_id": sheet_id, "sheet_tab": tab, "sheet_columns": json.dumps(header)})
    print("wrote sheet_id, sheet_tab, sheet_columns to config")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--adopt", metavar="SHEET_ID_OR_URL",
                    help="adopt the user's own sheet instead of creating one (matches + saves its columns)")
    ap.add_argument("--tab", default=None, help="tab name for --adopt (default: config sheet_tab, else Sheet1)")
    a = ap.parse_args(argv)
    if a.adopt:
        return adopt(a.adopt, a.tab, a.dry_run)
    cfg = jak_config.load()
    who = cfg.get("name") or "Candidate"
    updates: dict[str, str] = {}
    plan = []
    folder_id = cfg.get("drive_folder_id")
    if not folder_id:
        plan.append(f"create Drive folder 'Job Application Resumes - {who}'")
    if not cfg.get("drive_templates_folder_id"):
        plan.append("create Drive subfolder 'templates'")
    sheet_id = cfg.get("sheet_id")
    if not sheet_id:
        plan.append(f"create sheet 'Application Tracker - {who}' with 15 headers")
    if not plan:
        print("nothing to do: drive_folder_id, drive_templates_folder_id and sheet_id are already set")
        return 0
    for p in plan:
        print(("would " if a.dry_run else "") + p)
    if a.dry_run:
        return 0
    try:
        if not folder_id:
            folder_id = google.drive_mkdir(f"Job Application Resumes - {who}")["id"]
            updates["drive_folder_id"] = folder_id
        if not cfg.get("drive_templates_folder_id"):
            updates["drive_templates_folder_id"] = google.drive_mkdir("templates", folder_id)["id"]
        if not sheet_id:
            sh = google.sheet_create(f"Application Tracker - {who}")
            google.sheet_append(sh["id"], f"{cfg.get('sheet_tab') or 'Sheet1'}!A:O", [HEADERS])
            updates["sheet_id"] = sh["id"]
            print("tracker: " + sh.get("url", sh["id"]))
    finally:
        if updates:  # write whatever was created, even on a later failure
            jak_config.update_keys(jak_config.config_path(), updates)
            print("wrote to config: " + ", ".join(updates))
    return 0


if __name__ == "__main__":
    sys.exit(main())
