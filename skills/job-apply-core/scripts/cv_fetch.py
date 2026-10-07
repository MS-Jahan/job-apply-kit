#!/usr/bin/env python3
"""Decide HOW to read a CV source before the agent touches it.

A plain web fetch silently returns a truncated page for Google Docs links
(login/JS shell instead of content) — that is how CV setups end up built
from half a CV. This script classifies the source and prints the read plan
as JSON (plus human lines). It never fetches anything itself.

  cv_fetch.py <url-or-file-path> [--json-only]

kinds:
  local-file        read directly (PDF via pdfinfo/pdftotext, text as-is).
  google-docs       MUST be read through the debug browser (agent-browser
                    open + snapshot, scroll to the end): the user is already
                    logged in there. Requires BOOTSTRAP §3 done first.
                    Alternative once the Google backend exists: gog export.
  google-drive-file same as google-docs (open in the debug browser).
  web               try a plain fetch first; when the page looks truncated or
                    JS-gated, fall back to the debug browser.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DOCS_RE = re.compile(r"docs\.google\.com/document/d/([A-Za-z0-9_-]+)")
DRIVE_RE = re.compile(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:export=[^&]*&)?id=)([A-Za-z0-9_-]+)")


def classify(source: str) -> dict:
    """Pure classifier: source string -> read plan. No I/O besides stat."""
    s = (source or "").strip()
    if not s:
        return {"kind": "unknown", "method": "ask",
                "detail": "empty source — ask the user for the CV (URL or file path)."}
    if "/pub" in s and "docs.google.com" in s:
        return {"kind": "web", "method": "webfetch",
                "detail": "published Google Doc (public HTML) — plain fetch works; verify the full text arrived."}
    m = DOCS_RE.search(s)
    if m:
        return {"kind": "google-docs", "method": "debug-browser", "doc_id": m.group(1),
                "detail": "Google Doc — read ONLY through the debug browser (agent-browser open + snapshot to the end). "
                          "Plain web fetch returns a truncated page. Requires the debug browser first (BOOTSTRAP §3). "
                          "Alternative once the Google backend exists: export via gog."}
    m = DRIVE_RE.search(s)
    if m:
        return {"kind": "google-drive-file", "method": "debug-browser", "doc_id": m.group(1),
                "detail": "Google Drive file — open in the debug browser (user is logged in there) and read via snapshot. "
                          "Requires the debug browser first (BOOTSTRAP §3)."}
    if "://" not in s:
        p = Path(s).expanduser()
        if p.is_file():
            if p.suffix.lower() == ".pdf":
                return {"kind": "local-file", "method": "pdf",
                        "detail": f"local PDF — extract text (pdfinfo/pdftotext or Python), file: {p}"}
            return {"kind": "local-file", "method": "read",
                    "detail": f"local file — read directly: {p}"}
        return {"kind": "unknown", "method": "ask",
                "detail": f"not a URL and no such file ({s}) — ask the user to check the path."}
    return {"kind": "web", "method": "webfetch",
            "detail": "plain page — fetch it, confirm the FULL text arrived (contact block to last line); "
                      "when truncated or JS-gated, re-read through the debug browser."}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", default="", help="CV URL or local file path")
    ap.add_argument("--json-only", action="store_true", help="print only the JSON plan")
    a = ap.parse_args(argv)
    plan = classify(a.source)
    print(json.dumps(plan, indent=2))
    if not a.json_only:
        print(f"read via: {plan['method']} — {plan['detail']}")
    return 0 if plan["kind"] != "unknown" else 2


if __name__ == "__main__":
    sys.exit(main())
