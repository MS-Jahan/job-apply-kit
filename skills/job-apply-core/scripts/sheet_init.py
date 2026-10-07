#!/usr/bin/env python3
"""One-time setup for a new user: create the Drive folder, a `templates` subfolder and the tracker
sheet (with the 15 headers A..O), then write the ids into config.md. Existing ids are kept.

Usage: python3 sheet_init.py [--dry-run]
       python3 sheet_init.py --adopt SHEET_ID_OR_URL [--tab NAME] [--dry-run]
       python3 sheet_init.py --adopt-folder FOLDER_ID_OR_URL [--dry-run]

Agent procedure (ask-first — this script never prompts):
  1. Explain the two things: the SHEET ("Application Tracker") is where every
     application is tracked (one row per job, status moves Found → Applied);
     the DRIVE FOLDER ("Application Tracker") is where every generated resume,
     CV and cover letter is uploaded. Then ask: "Do you already have a tracker
     sheet or a Drive folder? Paste the URLs — or shall I create both?"
  2. URLs pasted → --adopt (sheet: matches + saves its columns) and/or
     --adopt-folder. Nothing matched → report it, ask the user, never guess.
  3. Nothing exists → run bare sheet_init.py: it creates the "Application Tracker"
     folder + templates subfolder + "Application Tracker" sheet in Drive root and
     writes all ids to config.

Needs a usable Google backend (see doctor.sh). Nothing is shared publicly here;
resume files are shared one by one at upload time, and only inside this folder.
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


def folder_id_from(s: str) -> str:
    m = re.search(r"/drive/(?:folders|file/d)/([A-Za-z0-9_-]+)", s)
    return m.group(1) if m else s.strip()


def adopt_folder(folder_ref: str, dry_run: bool) -> int:
    folder_id = folder_id_from(folder_ref)
    print(f"adopted Drive folder {folder_id} (uploads go here; resumes are shared one by one)")
    if dry_run:
        return 0
    jak_config.update_keys(jak_config.config_path(), {"drive_folder_id": folder_id})
    print("wrote drive_folder_id to config")
    return 0


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
    ap.add_argument("--adopt-folder", metavar="FOLDER_ID_OR_URL",
                    help="adopt the user's own Drive folder instead of creating one")
    ap.add_argument("--tab", default=None, help="tab name for --adopt (default: config sheet_tab, else Sheet1)")
    a = ap.parse_args(argv)
    if a.adopt:
        return adopt(a.adopt, a.tab, a.dry_run)
    if a.adopt_folder:
        return adopt_folder(a.adopt_folder, a.dry_run)
    cfg = jak_config.load()
    updates: dict[str, str] = {}
    plan = []
    folder_id = cfg.get("drive_folder_id")
    if not folder_id:
        plan.append("create Drive folder 'Application Tracker' (all resumes, CVs, cover letters upload here)")
    if not cfg.get("drive_templates_folder_id"):
        plan.append("create Drive subfolder 'templates'")
    sheet_id = cfg.get("sheet_id")
    if not sheet_id:
        plan.append("create sheet 'Application Tracker' with 15 headers (one row per application)")
    if not plan:
        print("nothing to do: drive_folder_id, drive_templates_folder_id and sheet_id are already set")
        return 0
    for p in plan:
        print(("would " if a.dry_run else "") + p)
    if a.dry_run:
        return 0
    try:
        if not folder_id:
            folder_id = google.drive_mkdir("Application Tracker")["id"]
            updates["drive_folder_id"] = folder_id
        if not cfg.get("drive_templates_folder_id"):
            updates["drive_templates_folder_id"] = google.drive_mkdir("templates", folder_id)["id"]
        if not sheet_id:
            sh = google.sheet_create("Application Tracker")
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
