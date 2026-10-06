import importlib, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

import _paths
from _paths import REPO

SK = REPO / "skills" / "bdjobs-full-run" / "scripts"
CFG = """## Identity
- **name:** Test User
## Auto-skip
- **max_experience_years:** 3
- **min_salary:** 20000
- **onsite_locations:** Springfield, Shelbyville
- **remote_ok:** true
- **salary_floor_remote:** 30000
- **salary_floor_onsite:** 40000
## Search terms
- **bdjobs_terms:** Rust, Go
"""


def load_bc(cfg_text, ws):
    p = Path(ws) / "c.md"
    p.write_text(cfg_text + "\n## Paths\n- **workspace:** %s\n" % ws)
    env = mock.patch.dict(os.environ, {"JAK_CONFIG": str(p)})
    env.start()
    sys.path.insert(0, str(SK))
    for m in ("bd_common",):
        sys.modules.pop(m, None)
    bc = importlib.import_module("bd_common")
    bc._SETTINGS = None
    return bc, env


class BdCommonTests(unittest.TestCase):
    def setUp(self):
        try:
            import websocket  # noqa: F401
        except ImportError:
            self.skipTest("websocket-client not installed")
        self.tmp = tempfile.TemporaryDirectory()
        self.bc, self.env = load_bc(CFG, self.tmp.name)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_settings_come_from_config(self):
        self.assertEqual(self.bc.SEARCH_TERMS, ["Rust", "Go"])
        self.assertEqual(self.bc.SALARY_FLOORS, {"remote": 30000, "onsite": 40000})
        self.assertEqual(self.bc.OK_LOCATIONS, ("springfield", "shelbyville"))
        self.assertEqual(self.bc.REPO, self.tmp.name)
        self.assertTrue(self.bc.CREDS_FILE.startswith(self.tmp.name))

    def test_run_dir_inside_workspace(self):
        self.assertTrue(self.bc.run_dir("2026-01-01").startswith(self.tmp.name))

    def test_auto_skip_rules_use_config(self):
        a = self.bc.auto_skip
        self.assertIn("4y", a(exp_years=4, location="Springfield"))
        self.assertIsNone(a(exp_years=3, location="Springfield"))
        self.assertIn("below 20000", a(salary_low=15000, location="Springfield"))
        self.assertIn("not in", a(location="Capital City"))
        self.assertIsNone(a(location="Capital City", remote=True))

    def test_salary_logic(self):
        c = self.bc.compute_salary
        self.assertEqual(c("BDT 45,000 - 70,000", False)[0], 45000)       # range above floor: anchor at low
        self.assertEqual(c("BDT 30,000 - 60,000", False)[0], 45000)       # crosses floor: midpoint
        self.assertEqual(c("Tk. 10000 - 20000", True)[0], 30000)          # below floor: floor
        self.assertEqual(c("Negotiable", False)[0], 40000)                # none: floor

    def test_missing_floor_is_an_error_not_a_hidden_default(self):
        self.env.stop()
        self.bc, self.env = load_bc(CFG.replace("- **salary_floor_onsite:** 40000\n", ""), self.tmp.name)
        with self.assertRaises(SystemExit):
            self.bc.compute_salary("Negotiable", False)

    def test_contact_and_display_helpers(self):
        self.assertEqual(self.bc.extract_contact("send CV to hr@example.org now"), "hr@example.org")
        self.assertEqual(self.bc.salary_display("", ""), "Negotiable")

    def test_sheet_append_shim_accepts_json_string_and_dict(self):
        import sheet_append
        with mock.patch.object(sheet_append, "append", return_value={"range": "r"}) as ap:
            self.bc.sheet_append('{"company": "A"}')
            self.bc.sheet_append({"company": "B"})
        self.assertEqual([c.args[0]["company"] for c in ap.call_args_list], ["A", "B"])

    def test_no_hardcoded_personal_tuning_in_scripts(self):
        for f in SK.glob("*.py"):
            text = f.read_text()
            for bad in ("OK_LOCATIONS = (", "ACCEPTED_LOCATIONS = (", "SEARCH_TERMS = [", "SALARY_FLOORS = {", "9222/", "drive_sheet", "JDs/tracker/gmail_draft"):
                self.assertNotIn(bad, text, f"{f.name}: {bad}")


class SkillScriptsCompile(unittest.TestCase):
    def test_all_scripts_compile(self):
        for f in SK.glob("*.py"):
            compile(f.read_text(), str(f), "exec")


if __name__ == "__main__":
    unittest.main()
