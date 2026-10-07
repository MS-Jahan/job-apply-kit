import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALL = str(REPO / "install.py")


def base_env(tmp):
    t = Path(tmp)
    return dict(os.environ,
                JAK_CLAUDE_BIN=str(t / "no-claude"),
                JAK_MANIFEST=str(t / "unused-manifest.json"),
                JAK_CONFIG=str(t / "none.md"),
                JAK_CLAUDE_CONFIG=str(t / "claude.json"),
                JAK_OPENCODE_CONFIG=str(t / "opencode.json"),
                JAK_TOOLS_FILE=str(t / "tools.json"))


def run(args, env):
    return subprocess.run([sys.executable, INSTALL] + args, capture_output=True, text=True, env=env)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = base_env(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_list_validates_every_skill(self):
        r = run(["--list"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("job-apply-core", r.stdout)
        self.assertIn("humanizer", r.stdout)

    def test_default_run_registers_mcp_and_records_tools(self):
        r = run([], self.env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        cc = json.loads(Path(self.env["JAK_CLAUDE_CONFIG"]).read_text())
        self.assertIn("chrome-devtools", cc["mcpServers"])
        oc = json.loads(Path(self.env["JAK_OPENCODE_CONFIG"]).read_text())
        self.assertIn("chrome-devtools", oc["mcp"])
        self.assertIn("in place, nothing copied", r.stdout)

    def test_no_mcp_flag_skips_registration(self):
        r = run(["--no-mcp"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertFalse(Path(self.env["JAK_CLAUDE_CONFIG"]).exists())
        self.assertFalse(Path(self.env["JAK_OPENCODE_CONFIG"]).exists())

    def test_no_path_flag_skips_tools_record(self):
        r = run(["--no-path"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertFalse(Path(self.env["JAK_TOOLS_FILE"]).exists())

    def test_dry_run_changes_nothing(self):
        r = run(["--dry-run"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        t = Path(self.tmp.name)
        self.assertFalse((t / "claude.json").exists())
        self.assertFalse((t / "opencode.json").exists())
        self.assertFalse((t / "tools.json").exists())

    def test_removed_copy_flags_are_rejected(self):
        for flag in (["--dest", "x"], ["--uninstall"], ["--link"], ["--target", "claude"]):
            r = run(flag, self.env)
            self.assertNotEqual(r.returncode, 0, flag)


if __name__ == "__main__":
    unittest.main()
