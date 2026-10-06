#!/usr/bin/env python3
"""Read the user's `templates_dir/INDEX.md` and pick the best template for a job post.

INDEX.md has one block per category:

  ## <CATEGORY>
  - **keywords:** comma list used to match a job post
  - **cv:** CV_<CAT>.tex / .pdf
  - **resume:** RESUME_<CAT>.tex / .pdf
  - **cover_letter:** CL_<CAT>.tex / .md / .pdf
  - **page_budget:** cv 2, resume 1, cl 1
  - **avoid_for:** short note

A value like `RESUME_X.tex / .pdf` expands to RESUME_X.tex and RESUME_X.pdf.

Usage:
  python3 template_index.py list
  python3 template_index.py match "<job post text>" [--kind resume|cv|cover_letter]
Prints JSON {category, score, file, templates_dir}; exit 1 when there is no usable template.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

HEADING = re.compile(r"^##\s+(.+?)\s*$")
KEYVAL = re.compile(r"^\s*[-*]\s+\*\*([A-Za-z0-9_]+):\*\*\s*(.*)$")
KINDS = ("cv", "resume", "cover_letter")


def expand(value: str) -> list[str]:
    """`A.tex / .pdf` -> ['A.tex', 'A.pdf']."""
    parts = [p.strip() for p in value.split("/") if p.strip()]
    if not parts:
        return []
    base = parts[0]
    stem = base.rsplit(".", 1)[0] if "." in base else base
    out = [base]
    for ext in parts[1:]:
        out.append(stem + ext if ext.startswith(".") else ext)
    return out


def parse_index(text: str) -> list[dict]:
    entries: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        h = HEADING.match(line)
        if h:
            cur = {"category": h.group(1).strip()}
            entries.append(cur)
            continue
        m = KEYVAL.match(line)
        if m and cur is not None:
            cur[m.group(1)] = m.group(2).strip()
    for e in entries:
        e["keywords"] = [k.strip().lower() for k in re.split(r"[,\n]", e.get("keywords", "")) if k.strip()]
        for kind in KINDS:
            e[kind + "_files"] = expand(e.get(kind, ""))
    return entries


def templates_dir() -> Path:
    import jak_config
    return jak_config.load().path("templates_dir")


def load(tdir: Path | None = None) -> list[dict]:
    tdir = Path(tdir) if tdir else templates_dir()
    idx = tdir / "INDEX.md"
    if not idx.is_file():
        return []
    return parse_index(idx.read_text(encoding="utf-8"))


def score(entry: dict, text: str) -> int:
    t = text.lower()
    total = 0
    for kw in entry["keywords"]:
        if re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", t):
            total += 1
    return total


def pick_file(entry: dict, kind: str, ext: str = ".pdf") -> str | None:
    return next((f for f in entry.get(kind + "_files", []) if f.lower().endswith(ext)), None)


def best_match(text: str, entries: list[dict], kind: str = "resume"):
    """Return (entry, score). Ties go to the first entry; zero score falls back to a 'full' category, else the first usable."""
    usable = [e for e in entries if pick_file(e, kind)]
    if not usable:
        return None, 0
    ranked = sorted(usable, key=lambda e: -score(e, text))
    top = ranked[0]
    s = score(top, text)
    if s == 0:
        fallback = next((e for e in usable if "full" in e["category"].lower()), usable[0])
        return fallback, 0
    return top, s


def resolve(text: str, kind: str = "resume", tdir: Path | None = None) -> dict | None:
    tdir = Path(tdir) if tdir else templates_dir()
    entry, s = best_match(text, load(tdir), kind)
    if not entry:
        return None
    f = pick_file(entry, kind)
    return {"category": entry["category"], "score": s, "file": str(tdir / f), "templates_dir": str(tdir)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    m = sub.add_parser("match")
    m.add_argument("text")
    m.add_argument("--kind", choices=KINDS, default="resume")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "list":
            for e in load():
                print(f"{e['category']}: {', '.join(e['keywords'])}")
            return 0
        r = resolve(a.text, a.kind)
    except Exception as ex:  # noqa: BLE001
        print(f"ERROR: {ex}", file=sys.stderr)
        return 1
    if not r:
        print("ERROR: no usable template in templates_dir (add INDEX.md or run /create-template)", file=sys.stderr)
        return 1
    print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
