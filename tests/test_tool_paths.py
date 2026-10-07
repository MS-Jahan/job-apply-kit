import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "skills" / "job-apply-core" / "scripts"))

import tool_paths
import doctor


def make_exe(d: Path, name: str) -> Path:
    for candidate in (name, name + ".exe"):
        p = d / candidate
        p.write_text("fake")
        try:
            p.chmod(p.stat().st_mode | stat.S_IEXEC)
        except OSError:
            pass
    return d / (name + ".exe")


class ToolPathsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        self.tools = self.t / "tools.json"
        self.old_env = dict(os.environ)
        os.environ["JAK_TOOLS_FILE"] = str(self.tools)

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.clear()
        os.environ.update(self.old_env)

    def test_record_and_load_roundtrip(self):
        bindir = self.t / "bin"
        bindir.mkdir()
        make_exe(bindir, "pdfinfo")
        os.environ["PATH"] = str(bindir) + os.pathsep + os.environ.get("PATH", "")
        merged = tool_paths.record()
        self.assertIn("pdfinfo", merged)
        self.assertEqual(tool_paths.load(), merged)
        self.assertTrue(self.tools.is_file())

    def test_load_missing_file_is_empty(self):
        os.environ["JAK_TOOLS_FILE"] = str(self.t / "nope.json")
        self.assertEqual(tool_paths.load(), {})

    def test_missing_from_path_and_dry_run(self):
        bindir = self.t / "bin"
        bindir.mkdir()
        orig_dirs = tool_paths.user_bin_dirs
        tool_paths.user_bin_dirs = lambda: [bindir]  # noqa: E731
        try:
            os.environ["PATH"] = os.pathsep.join(
                p for p in os.environ.get("PATH", "").split(os.pathsep) if p != str(bindir))
            self.assertEqual(tool_paths.missing_from_path(), [bindir])
            changed, msgs = tool_paths.ensure_on_path(dry=True)
            self.assertTrue(changed)
            self.assertTrue(msgs)
            self.assertFalse(self.tools.exists())
        finally:
            tool_paths.user_bin_dirs = orig_dirs

    def test_doctor_falls_back_to_tools_json(self):
        fake = make_exe(self.t, "pdfinfo")
        tool_paths.save({"pdfinfo": str(fake)})
        self.assertEqual(doctor.saved_tool_path("pdfinfo"), str(fake))
        self.assertEqual(doctor.which("pdfinfo"), str(fake))

    def test_doctor_unknown_tool_is_none(self):
        self.assertIsNone(doctor.saved_tool_path("no-such-tool-xyz"))

    def test_install_no_path_flag(self):
        env = dict(os.environ, JAK_TOOLS_FILE=str(self.t / "t2.json"),
                   JAK_CONFIG=str(self.t / "none.md"))
        r = subprocess.run([sys.executable, str(REPO / "install.py"), "--no-path", "--no-mcp"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertFalse((self.t / "t2.json").exists())


if __name__ == "__main__":
    unittest.main()
