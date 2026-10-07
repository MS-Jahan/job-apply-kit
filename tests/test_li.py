import importlib, os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

import _paths
from _paths import REPO

SK = REPO / "skills" / "linkedin-full-run" / "scripts"
CFG = """## Identity
- **name:** Test User
- **name_file:** Test_User
- **phone:** +15550001111
- **email_header:** test@example.org
## Auto-skip
- **max_experience_years:** 4
- **min_salary:** 20000
- **currency:** USD
- **onsite_locations:** Springfield
## Search terms
- **linkedin_queries:**
    "Rust" AND (hiring OR vacancy), with comma
    "Go" AND hiring
"""


def load_L(ws, extra=""):
    p = Path(ws) / "c.md"
    p.write_text(CFG + extra + "\n## Paths\n- **workspace:** %s\n" % ws)
    env = mock.patch.dict(os.environ, {"JAK_CONFIG": str(p)})
    env.start()
    sys.path.insert(0, str(SK))
    for m in ("li_common", "li3_apply"):
        sys.modules.pop(m, None)
    L = importlib.import_module("li_common")
    L._SETTINGS = None
    return L, env


class LiTests(unittest.TestCase):
    def setUp(self):
        try:
            import websocket  # noqa: F401
        except ImportError:
            self.skipTest("websocket-client not installed")
        self.tmp = tempfile.TemporaryDirectory()
        self.L, self.env = load_L(self.tmp.name)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_queries_from_config_keep_commas(self):
        self.assertEqual(self.L.SEARCH_QUERIES, ['"Rust" AND (hiring OR vacancy), with comma', '"Go" AND hiring'])

    def test_workspace_paths(self):
        self.assertTrue(self.L.run_dir("2026-01-01").startswith(self.tmp.name))
        self.assertTrue(self.L.cache_root().startswith(self.tmp.name))

    def test_auto_skip_uses_config(self):
        a = self.L.auto_skip
        self.assertTrue(a({"experience": "5 years"})[0])
        self.assertFalse(a({"experience": "4 years", "remote": "yes"})[0])
        skip, why = a({"salary_raw": "BDT 15,000", "remote": "yes"})
        self.assertTrue(skip); self.assertIn("20000", why)
        self.assertTrue(a({"location": "Capital City", "remote": "no"})[0])
        self.assertFalse(a({"location": "Springfield", "remote": "no"})[0])

    def test_history_paths_survive_missing_tracker_dir(self):
        self.assertEqual(self.L.application_history_paths(), [])

    def test_now_local_returns_text(self):
        self.assertRegex(self.L.now_local(), r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}")

    def test_signature_and_body_rules(self):
        import li3_apply as A
        row = {"company": "Acme", "position": "Dev"}
        rd = Path(self.tmp.name) / "run"; (rd / "bodies").mkdir(parents=True)
        self.assertEqual(A._email_body(str(rd), row, {}, "x@y.z"), "")            # no body file: refused
        g = A._email_body(str(rd), row, {}, "x@y.z", allow_generic=True)
        self.assertIn("Test User", g); self.assertIn("test@example.org", g)
        for claim in ("Python", "Django", "PostgreSQL", "React", "Docker"):         # no hard-coded skills
            self.assertNotIn(claim, g)
        (rd / "bodies" / "acme.txt").write_text("custom body")
        self.assertEqual(A._email_body(str(rd), row, {}, "x@y.z"), "custom body")
        self.assertEqual(A._email_subject(str(rd), row, "Dev"), "Application for Dev - Test User")

    def test_scripts_have_no_hardcoded_personal_values(self):
        for f in SK.glob("*.py"):
            text = f.read_text()
            for bad in ("drive_sheet", "templates_library", "JDs/bdjobs", "now_dhaka", "9222/"):
                self.assertNotIn(bad, text, f"{f.name}: {bad}")


class TemplateIndexTests(unittest.TestCase):
    def test_match_and_fallback(self):
        import template_index as t
        e = t.parse_index("## PYTHON\n- **keywords:** python, django\n- **resume:** RESUME_PY.tex / .pdf\n"
                          "## FULLSTACK\n- **keywords:** react\n- **resume:** RESUME_FS.tex / .pdf\n")
        self.assertEqual(t.best_match("We need Django and Python", e)[0]["category"], "PYTHON")
        self.assertEqual(t.best_match("COBOL role", e)[0]["category"], "FULLSTACK")   # zero score -> full-stack fallback
        self.assertEqual(t.pick_file(e[0], "resume"), "RESUME_PY.pdf")
        self.assertEqual(t.expand("A.tex / .pdf / .md"), ["A.tex", "A.pdf", "A.md"])

    def test_whole_word_matching(self):
        import template_index as t
        e = t.parse_index("## JS\n- **keywords:** java\n- **resume:** R.tex / .pdf\n")
        self.assertEqual(t.score(e[0], "javascript developer"), 0)
        self.assertEqual(t.score(e[0], "java developer"), 1)

    def test_no_pdf_means_no_template(self):
        import template_index as t
        e = t.parse_index("## X\n- **keywords:** a\n- **resume:** R.tex\n")
        self.assertEqual(t.best_match("a", e), (None, 0))


class ConfigPlaceholderTests(unittest.TestCase):
    def test_placeholder_continuation_is_unset(self):
        import jak_config
        v = jak_config.parse("## S\n- **linkedin_queries:**\n    <one query per line>\n- **x:** y\n")
        self.assertEqual(v["linkedin_queries"], "")
        self.assertEqual(v["x"], "y")


if __name__ == "__main__":
    unittest.main()
