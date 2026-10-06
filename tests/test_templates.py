"""Checks on the shipped fictional example templates and the create-template skill."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths
from _paths import REPO

EX = REPO / "examples" / "templates"
CATEGORIES = ["PYTHON_BACKEND", "FRONTEND", "FULLSTACK"]
PAGE_BUDGET = {"CV": 2, "RESUME": 1, "CL": 1}


def pdfinfo_pages(pdf: Path) -> int | None:
    if not shutil.which("pdfinfo"):
        return None
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    return int(m.group(1)) if m else None


class ExampleTemplateTests(unittest.TestCase):
    def test_index_lists_all_three_categories_with_existing_files(self):
        index = (EX / "INDEX.md").read_text()
        for cat in CATEGORIES:
            self.assertIn(f"## {cat}", index)
        import sys as _s
        _s.path.insert(0, str(REPO / "skills" / "job-apply-core" / "scripts"))
        import template_index as t
        entries = {e["category"]: e for e in t.load(EX)}
        self.assertEqual(set(entries), set(CATEGORIES))
        for cat, e in entries.items():
            for kind in ("cv", "resume", "cover_letter"):
                for f in e[kind + "_files"]:
                    self.assertTrue((EX / f).exists(), f"{cat}: missing {f}")

    def test_no_em_dash_anywhere(self):
        # LaTeX comments (after an unescaped %) never render, so they are exempt; the compiled
        # document itself (and the .md cover letters) must have zero em-dashes (OPERATIONS #format).
        for f in list(EX.glob("*.tex")) + list(EX.glob("*.md")):
            is_tex = f.suffix == ".tex"
            for line in f.read_text(encoding="utf-8").splitlines():
                code = line.split("%", 1)[0] if is_tex else line
                self.assertNotIn("—", code, f"{f.name}: {line!r}")       # em-dash
                self.assertNotIn("---", code, f"{f.name}: {line!r}")     # LaTeX's rendered em-dash

    def test_fictional_people_not_real(self):
        names = {"Alex Rivera", "Priya Nakamura", "Jordan Takahashi"}
        found = set()
        for f in EX.glob("*.tex"):
            text = f.read_text()
            for n in names:
                if n in text:
                    found.add(n)
        self.assertEqual(found, names)
        # and none of these fictional files mention a real contact domain
        for f in EX.glob("*.tex"):
            self.assertIn("example.com", f.read_text())

    @unittest.skipUnless(shutil.which("tectonic"), "tectonic not installed")
    def test_compiles_to_the_right_page_count(self):
        with tempfile.TemporaryDirectory() as d:
            for tex in EX.glob("*.tex"):
                dst = Path(d) / tex.name
                shutil.copy(tex, dst)
                r = subprocess.run(["tectonic", "-X", "compile", str(dst)], capture_output=True, text=True, cwd=d)
                self.assertEqual(r.returncode, 0, f"{tex.name}: {r.stderr[-500:]}")
                kind = tex.stem.split("_")[0]  # CV / RESUME / CL
                want = PAGE_BUDGET.get(kind)
                if want is not None:
                    pages = pdfinfo_pages(Path(d) / (tex.stem + ".pdf"))
                    if pages is not None:
                        self.assertEqual(pages, want, tex.name)


class WithExamplesInstallTests(unittest.TestCase):
    def test_with_examples_copies_into_empty_templates_dir(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            tpl = Path(d) / "templates"
            env = dict(os.environ, JAK_TEMPLATES_DIR=str(tpl), JAK_MANIFEST=str(Path(d) / "m.json"))
            r = subprocess.run([sys.executable, str(REPO / "install.py"), "--dest", str(Path(d) / "skills"),
                               "job-apply-core", "--with-examples", "--no-mcp"],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((tpl / "INDEX.md").is_file())
            self.assertTrue((tpl / "CV_FULLSTACK.pdf").is_file())

    def test_with_examples_does_not_overwrite_a_nonempty_templates_dir(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            tpl = Path(d) / "templates"
            tpl.mkdir()
            (tpl / "mine.tex").write_text("real content")
            env = dict(os.environ, JAK_TEMPLATES_DIR=str(tpl), JAK_MANIFEST=str(Path(d) / "m.json"))
            subprocess.run([sys.executable, str(REPO / "install.py"), "--dest", str(Path(d) / "skills"),
                           "job-apply-core", "--with-examples", "--no-mcp"],
                           capture_output=True, text=True, env=env)
            self.assertFalse((tpl / "INDEX.md").exists())
            self.assertEqual((tpl / "mine.tex").read_text(), "real content")


if __name__ == "__main__":
    unittest.main()
