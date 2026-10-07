import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = str(REPO / "skills" / "job-apply-core" / "scripts" / "browser_setup.py")

sys.path.insert(0, str(REPO / "skills" / "job-apply-core" / "scripts"))
import browser_setup


def fake_env(tmp: Path, *names: str) -> dict:
    env = dict(os.environ)
    for n in names:
        fake = tmp / f"fake-{n}.exe"
        fake.write_text("fake")
        env[f"JAK_BROWSER_BIN_{n.upper()}"] = str(fake)
    return env


class BrowserSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_detect_finds_overrides_in_priority_order(self):
        # Machine-independent: the overridden browsers must be present and
        # correctly ordered relative to each other (real installs may add more).
        env = fake_env(self.t, "brave", "chrome")
        old = dict(os.environ)
        os.environ.update(env)
        try:
            found = browser_setup.detect()
        finally:
            os.environ.clear()
            os.environ.update(old)
        names = [f["name"] for f in found]
        self.assertIn("chrome", names)
        self.assertIn("brave", names)
        self.assertLess(names.index("chrome"), names.index("brave"))
        self.assertTrue(all(Path(f["path"]).is_file() for f in found))

    def test_suggest_prefers_first_and_none_when_empty(self):
        self.assertEqual(
            browser_setup.suggest([{"name": "brave"}, {"name": "chrome"}])["name"], "brave"
        )
        self.assertIsNone(browser_setup.suggest([]))

    def test_launcher_content_has_binary_port_profile(self):
        text = browser_setup.render_launcher("chrome", "/fake/chrome", 9223, "/fake/profile")
        self.assertIn("/fake/chrome", text)
        self.assertIn("9223", text)
        self.assertIn("/fake/profile", text)
        self.assertIn("--remote-debugging-port", text)
        self.assertIn("--user-data-dir", text)

    def test_list_json(self):
        env = fake_env(self.t, "chrome", "edge")
        r = subprocess.run([sys.executable, SCRIPT, "--list", "--json"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["suggested"], "chrome")
        names = sorted(b["name"] for b in data["browsers"])
        self.assertIn("chrome", names)
        self.assertIn("edge", names)

    def test_create_writes_launchers_and_desktop_shortcuts(self):
        env = fake_env(self.t, "chrome", "brave")
        out, desk = self.t / "launch", self.t / "desk"
        r = subprocess.run([sys.executable, SCRIPT, "--browser", "chrome,brave", "--create",
                            "--out-dir", str(out), "--desktop-dir", str(desk),
                            "--port", "9223"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        launchers = sorted(out.glob("browser-debug-*"))
        self.assertEqual(len(launchers), 2)
        for lf in launchers:
            self.assertIn("9223", lf.read_text(encoding="utf-8"))
        self.assertTrue(any(desk.iterdir()), "expected desktop shortcuts")

    def test_create_single_browser_only(self):
        env = fake_env(self.t, "chrome", "brave")
        out, desk = self.t / "launch", self.t / "desk"
        r = subprocess.run([sys.executable, SCRIPT, "--browser", "brave", "--create",
                            "--out-dir", str(out), "--desktop-dir", str(desk)],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(len(list(out.glob("browser-debug-*"))), 1)

    def test_unknown_browser_rejected(self):
        env = fake_env(self.t, "chrome")
        r = subprocess.run([sys.executable, SCRIPT, "--browser", "firefox", "--create",
                            "--out-dir", str(self.t)],
                           capture_output=True, text=True, env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown browser", r.stderr + r.stdout)

    def test_dry_run_writes_nothing(self):
        env = fake_env(self.t, "chrome")
        out, desk = self.t / "launch", self.t / "desk"
        r = subprocess.run([sys.executable, SCRIPT, "--browser", "all", "--create",
                            "--out-dir", str(out), "--desktop-dir", str(desk),
                            "--dry-run"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertFalse(out.exists())
        self.assertFalse(desk.exists())


if __name__ == "__main__":
    unittest.main()
