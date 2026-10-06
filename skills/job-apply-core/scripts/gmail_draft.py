#!/usr/bin/env python3
"""Create a Gmail DRAFT (never sent) with optional attachments, through google.py.

Usage:
  python3 gmail_draft.py --to a@b.com --subject "S" (--body "text" | --body-file F) \
      [--attach /path/file.pdf ...] [--cc x@y.com] [--bcc z@y.com]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jak_google as google  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--to", required=True)
    p.add_argument("--subject", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--body")
    g.add_argument("--body-file")
    p.add_argument("--cc", default="")
    p.add_argument("--bcc", default="")
    p.add_argument("--attach", action="append", default=[])
    a = p.parse_args(argv)
    body = a.body if a.body is not None else (sys.stdin.read() if a.body_file == "-" else Path(a.body_file).read_text(encoding="utf-8"))
    try:
        r = google.draft(a.to, a.subject, body, a.attach, a.cc, a.bcc)
    except google.GoogleError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"DRAFT_CREATED id={r['draft_id']} to={a.to} attach={','.join(a.attach) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
