import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALL = str(REPO / "install.py")

FAKE_CLAUDE = """import os, sys
base = os.path.dirname(os.path.abspath(__file__))
state = os.path.join(base, "state"); log = os.path.join(base, "log")
if sys.argv[1:3] == ["mcp", "get"]:
    sys.exit(0 if os.path.exists(state) else 1)
if sys.argv[1:3] == ["mcp", "add"]:
    open(log, "a").write(" ".join(sys.argv) + "\\n")
    open(state, "w").write("x")
    sys.exit(0)
sys.exit(2)
"""


class McpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.claude = t / "fake_claude.py"
        self.claude.write_text(FAKE_CLAUDE)
        self.oc = t / "opencode.json"
        self.cc = t / "claude.json"
        self.env = dict(os.environ, JAK_CLAUDE_BIN=str(self.claude),
                        JAK_MANIFEST=str(t / "m.json"), JAK_CONFIG=str(t / "none.md"),
                        JAK_CLAUDE_CONFIG=str(self.cc), JAK_OPENCODE_CONFIG=str(self.oc))

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
        self.assertFalse(self.cc.exists())

    def test_missing_files_are_created(self):
        env = dict(self.env)
        env.pop("JAK_CLAUDE_BIN", None)  # no CLI -> direct file edit
        r = subprocess.run([sys.executable, INSTALL, "--setup-mcp-only"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        cc = json.loads(self.cc.read_text())
        self.assertIn("chrome-devtools", cc["mcpServers"])
        self.assertEqual(cc["mcpServers"]["chrome-devtools"]["command"], "npx")
        oc = json.loads(self.oc.read_text())
        self.assertIn("chrome-devtools", oc["mcp"])
        self.assertEqual(oc["mcp"]["chrome-devtools"]["command"][0], "npx")

    def test_existing_claude_entry_not_overwritten(self):
        mine = {"command": "custom", "args": []}
        self.cc.write_text(json.dumps({"mcpServers": {"chrome-devtools": mine}}))
        self.oc.write_text("{}")
        self.run_mcp()
        self.assertEqual(json.loads(self.cc.read_text())["mcpServers"]["chrome-devtools"], mine)

    def test_opencode_v2_shape_supported(self):
        self.oc.write_text(json.dumps({"mcp": {"servers": {"other": {"type": "local", "command": ["x"]}}}}))
        self.run_mcp()
        cfg = json.loads(self.oc.read_text())
        self.assertIn("chrome-devtools", cfg["mcp"]["servers"])
        self.assertIn("other", cfg["mcp"]["servers"])

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
