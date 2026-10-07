"""Scripts must work from the repo checkout (skills are used in place, never copied)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths
from _paths import REPO

CFG = """## Identity
- **name:** Test User
- **name_file:** Test_User
- **email_header:** t@example.org
- **email_google:** t@example.org
## Sources
- **cv_source:** https://example.org/cv
## Auto-skip
- **salary_floor_remote:** 30000
- **salary_floor_onsite:** 40000
"""


def run(args, env, cwd):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, env=env, cwd=cwd)


class RepoLayoutTests(unittest.TestCase):
    def setUp(self):
        try:
            import websocket  # noqa: F401
        except ImportError:
            self.skipTest("websocket-client not installed")
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.ws = t / "ws"; self.ws.mkdir()
        (t / "c.md").write_text(CFG + "\n## Paths\n- **workspace:** %s\n" % self.ws)
        self.env = dict(os.environ, JAK_CONFIG=str(t / "c.md"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_repo_scripts_run(self):
        core = REPO / "skills" / "job-apply-core" / "scripts"
        li = REPO / "skills" / "linkedin-full-run" / "scripts"
        scripts = [
            [str(core / "jak_config.py"), "--check"],
            [str(REPO / "skills" / "bdjobs-full-run" / "scripts" / "bd3_filter_apply.py"),
             "salary", "--text", "BDT 45,000 - 70,000"],
            [str(li / "li3_apply.py"), "--help"],
            [str(li / "li1_extract.py"), "--help"],
            [str(REPO / "skills" / "check-discord-jobs" / "scripts" / "scan_channel.py"), "--help"],
            [str(core / "sheet_append.py"), "append", '{"company": "A"}', "--dry-run"],
            [str(core / "template_index.py"), "list"],
        ]
        for args in scripts:
            r = run(args, self.env, str(self.ws))
            self.assertEqual(r.returncode, 0, f"{Path(args[0]).name}: {r.stderr[-300:]}{r.stdout[-200:]}")
        r = run([str(REPO / "skills" / "bdjobs-full-run" / "scripts" / "bd3_filter_apply.py"),
                 "salary", "--text", "BDT 45,000 - 70,000"], self.env, str(self.ws))
        self.assertIn("45000", r.stdout)


if __name__ == "__main__":
    unittest.main()
