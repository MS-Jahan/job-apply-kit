#!/usr/bin/env python3
"""Read-only snapshot of the tracker sheet -> markdown + raw JSON in <workspace>/JDs/tracker/.

Usage: python3 sheet_snapshot.py [YYYY-MM-DD]
Writes sheet_snapshot_<date>.md and sheet_raw_<date>.json. Skills use it as the dedup fact base.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jak_google as google  # noqa: E402
import jak_config  # noqa: E402


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    date = argv[0] if argv else datetime.date.today().isoformat()
    cfg = jak_config.load()
    sheet_id, tab = cfg.require("sheet_id"), cfg.get("sheet_tab") or "Sheet1"
    out_dir = cfg.path("workspace") / "JDs" / "tracker"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = google.sheet_get(sheet_id, f"{tab}!A:O")
    (out_dir / f"sheet_raw_{date}.json").write_text(json.dumps(rows, indent=1))
    lines = ["# Application Tracker Snapshot (Google Sheet)", "",
             f"- **Source:** https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
             f"- **Snapshot date:** {date}", f"- **Total rows (incl header):** {len(rows)}", "",
             "| Row | Date | Company | Position | Status | How Applied | Deadline |", "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows[1:], start=2):
        r = r + [""] * (15 - len(r))
        lines.append(f"| {i} | {r[0]} | {r[1]} | {r[2]} | {r[9]} | {r[10]} | {r[13]} |")
    (out_dir / f"sheet_snapshot_{date}.md").write_text("\n".join(lines) + "\n")
    print(f"ROWS {len(rows)} -> {out_dir / f'sheet_snapshot_{date}.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
