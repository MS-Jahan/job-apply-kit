import json, os, stat, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALL = str(REPO / "install.py")

FAKE_CLAUDE = """#!/usr/bin/env bash
state="$(dirname "$0")/state"; log="$(dirname "$0")/log"
if [ "$1 $2" = "mcp get" ]; then [ -f "$state" ] && exit 0 || exit 1; fi
if [ "$1 $2" = "mcp add" ]; then echo "$@" >> "$log"; touch "$state"; exit 0; fi
exit 2
"""


class McpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.claude = t / "claude"
        self.claude.write_text(FAKE_CLAUDE)
        self.claude.chmod(self.claude.stat().st_mode | stat.S_IEXEC)
        self.oc = t / "opencode.json"
        self.env = dict(os.environ, JAK_CLAUDE_BIN=str(self.claude), JAK_OPENCODE_CONFIG=str(self.oc),
                        JAK_MANIFEST=str(t / "m.json"), JAK_CONFIG=str(t / "none.md"))

    def tearDown(self):
        self.tmp.cleanup()

    def run_mcp(self, *extra):
        return subprocess.run([sys.executable, INSTALL, "--setup-mcp-only", *extra], capture_output=True, text=True, env=self.env)

    def test_registers_in_claude_once(self):
        r = self.run_mcp()
        self.assertEqual(r.returncode, 0, r.stderr)
        log = (self.claude.parent / "log").read_text()
        self.assertIn("chrome-devtools", log)
        self.assertIn("-s user", log)
        self.assertIn("http://127.0.0.1:9222", log)
        r2 = self.run_mcp()
        self.assertIn("already registered in Claude Code", r2.stdout)
        self.assertEqual(len((self.claude.parent / "log").read_text().splitlines()), 1)

    def test_opencode_entry_added_and_existing_kept(self):
        self.oc.write_text(json.dumps({"mcp": {"other": {"type": "local", "command": ["x"]}}}))
        self.run_mcp()
        cfg = json.loads(self.oc.read_text())
        self.assertIn("chrome-devtools", cfg["mcp"])
        self.assertIn("other", cfg["mcp"])
        self.assertEqual(cfg["mcp"]["chrome-devtools"]["command"][0], "npx")
        self.assertTrue(Path(str(self.oc) + ".jak-backup").exists())

    def test_existing_opencode_entry_not_overwritten(self):
        mine = {"type": "local", "command": ["custom"]}
        self.oc.write_text(json.dumps({"mcp": {"chrome-devtools": mine}}))
        self.run_mcp()
        self.assertEqual(json.loads(self.oc.read_text())["mcp"]["chrome-devtools"], mine)

    def test_dry_run_changes_nothing(self):
        self.oc.write_text("{}")
        self.run_mcp("--dry-run")
        self.assertFalse((self.claude.parent / "log").exists())
        self.assertEqual(self.oc.read_text(), "{}")

    def test_install_with_dest_does_not_touch_mcp(self):
        d = Path(self.tmp.name) / "skills"
        subprocess.run([sys.executable, INSTALL, "--dest", str(d)], capture_output=True, text=True, env=self.env)
        self.assertFalse((self.claude.parent / "log").exists())

    def test_server_definition_valid(self):
        data = json.loads((REPO / "mcp" / "servers.json").read_text())
        spec = data["chrome-devtools"]
        self.assertEqual(spec["command"], "npx")
        self.assertIn("{{CDP_PORT}}", " ".join(spec["args"]))


if __name__ == "__main__":
    unittest.main()
