"""Scripts must work from an INSTALLED copy (skills dir as siblings), not just from the repo."""
import os, subprocess, sys, tempfile, unittest
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


class InstalledLayoutTests(unittest.TestCase):
    def setUp(self):
        try:
            import websocket  # noqa: F401
        except ImportError:
            self.skipTest("websocket-client not installed")
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.ws = t / "ws"; self.ws.mkdir()
        (t / "c.md").write_text(CFG + "\n## Paths\n- **workspace:** %s\n" % self.ws)
        self.env = dict(os.environ, JAK_CONFIG=str(t / "c.md"), JAK_MANIFEST=str(t / "m.json"))

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, *extra):
        dest = Path(self.tmp.name) / "skills"
        r = run([str(REPO / "install.py"), "--dest", str(dest), *extra], self.env, str(REPO))
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return dest

    def check_all(self, dest):
        scripts = [
            [str(dest / "job-apply-core/scripts/jak_config.py"), "--check"],
            [str(dest / "bdjobs-full-run/scripts/bd3_filter_apply.py"), "salary", "--text", "BDT 45,000 - 70,000"],
            [str(dest / "li-full-run/scripts/li3_apply.py"), "--help"],
            [str(dest / "li-full-run/scripts/li1_extract.py"), "--help"],
            [str(dest / "check-discord-jobs/scripts/scan_channel.py"), "--help"],
            [str(dest / "job-apply-core/scripts/sheet_append.py"), "append", '{"company": "A"}', "--dry-run"],
            [str(dest / "job-apply-core/scripts/template_index.py"), "list"],
        ]
        for args in scripts:
            r = run(args, self.env, str(self.ws))
            self.assertEqual(r.returncode, 0, f"{Path(args[0]).name}: {r.stderr[-300:]}{r.stdout[-200:]}")
        r = run([str(dest / "bdjobs-full-run/scripts/bd3_filter_apply.py"), "salary", "--text", "BDT 45,000 - 70,000"], self.env, str(self.ws))
        self.assertIn("45000", r.stdout)

    def test_copy_install(self):
        self.check_all(self.install())

    def test_link_install(self):
        self.check_all(self.install("--link"))

    def test_skill_text_has_no_unrendered_tokens(self):
        dest = self.install()
        for md in dest.rglob("*.md"):
            self.assertNotIn("{{", md.read_text(encoding="utf-8"), str(md))


if __name__ == "__main__":
    unittest.main()
