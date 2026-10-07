#!/usr/bin/env python3
"""Prove the Google connection works, right after authentication (read-only).

Three checks, three items each — the agent shows this output to the user as
the "connection is live" evidence:
  1. Gmail: newest 3 messages (id + subject).
  2. Drive: newest 3 files in the user's Drive (name + type).
  3. Sheets: newest 3 spreadsheets.

Usage: python3 google_verify.py [--limit 3] [--json]
Exit 0 = all three answered. Exit 1 = a check failed (auth, scope or network);
the failing section names its error so the agent knows what to fix.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

SHEETS_MIME = "application/vnd.google-apps.spreadsheet"


def verify(limit: int = 3, **kw) -> dict:
    import jak_google as google
    report: dict = {"backend": None, "checks": {}, "ok": False}
    try:
        report["backend"] = google.backend(**kw).name
    except Exception as e:  # noqa: BLE001
        report["checks"]["backend"] = {"ok": False, "error": str(e)[:300]}
        return report
    try:
        msgs = google.gmail_list(limit, **kw)
        report["checks"]["gmail"] = {"ok": True, "messages": msgs}
    except Exception as e:  # noqa: BLE001
        report["checks"]["gmail"] = {"ok": False, "error": str(e)[:300]}
    try:
        files = google.drive_list(limit, **kw)
        report["checks"]["drive"] = {"ok": True, "files": files}
    except Exception as e:  # noqa: BLE001
        report["checks"]["drive"] = {"ok": False, "error": str(e)[:300]}
    try:
        sheets = google.drive_list(limit, f"mimeType='{SHEETS_MIME}' and trashed=false", **kw)
        report["checks"]["sheets"] = {"ok": True, "sheets": sheets}
    except Exception as e:  # noqa: BLE001
        report["checks"]["sheets"] = {"ok": False, "error": str(e)[:300]}
    report["ok"] = all(c.get("ok") for c in report["checks"].values())
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--json", action="store_true", help="print only the JSON report")
    ap.add_argument("--backend", choices=["auto", "gog", "python"])
    ap.add_argument("--account")
    a = ap.parse_args(argv)
    kw = {k: v for k, v in (("name", a.backend if a.backend and a.backend != "auto" else None),
                            ("account", a.account)) if v}
    rep = verify(a.limit, **kw)
    print(json.dumps(rep, indent=2))
    if not a.json:
        for name, c in rep["checks"].items():
            if c.get("ok"):
                items = c.get("messages") or c.get("files") or c.get("sheets") or []
                print(f"{name}: OK ({len(items)} shown)")
                for it in items:
                    print(f"  - {it.get('subject') or it.get('name') or it.get('id')}")
            else:
                print(f"{name}: FAILED — {c.get('error')}")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
