#!/usr/bin/env python3
"""One-time setup for a new user: create the Drive folder, a `templates` subfolder and the tracker
sheet (with the 15 headers A..O), then write the ids into config.md. Existing ids are kept.

Usage: python3 sheet_init.py [--dry-run]
Needs a usable Google backend (see doctor.sh). Nothing is shared publicly here; resume files are
shared one by one at upload time, and only inside this folder.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jak_google as google  # noqa: E402
import jak_config  # noqa: E402
from sheet_append import HEADERS  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
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
