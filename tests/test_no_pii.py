"""Scan the repository for personal data using patterns from a PRIVATE file.

Set JAK_PII_PATTERNS to a file with one regex per line (names, phone, emails, ids, hostnames).
The file must never live in this repository. Without it the test is skipped with a notice;
run it locally before every commit.
"""
import os, re, unittest
from pathlib import Path

import _paths
from _paths import REPO

SKIP_DIRS = {".git", "__pycache__"}


class NoPiiTests(unittest.TestCase):
    def test_repo_has_no_personal_patterns(self):
        f = os.environ.get("JAK_PII_PATTERNS")
        if not f or not Path(f).is_file():
            self.skipTest("JAK_PII_PATTERNS not set: run with a private pattern file before committing")
        pats = [re.compile(l.strip(), re.I) for l in Path(f).read_text().splitlines() if l.strip() and not l.startswith("#")]
        hits = []
        for p in REPO.rglob("*"):
            if p.is_file() and not (set(p.parts) & SKIP_DIRS):
                try:
                    text = p.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue
                for rx in pats:
                    if rx.search(text):
                        hits.append(f"{p.relative_to(REPO)}: {rx.pattern}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
