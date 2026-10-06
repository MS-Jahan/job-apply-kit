import os, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class DoctorTests(unittest.TestCase):
    def test_runs_and_reports_missing_config(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, JAK_CONFIG=str(Path(d) / "nope.md"))
            r = subprocess.run([sys.executable, str(REPO / "doctor.py"), "--mode", "tailor"], capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 1)
            self.assertIn("MISSING", r.stdout)
            self.assertIn("config file", r.stdout)

    def test_passes_config_check_with_valid_config(self):
        sample = (REPO / "tests" / "test_config.py").read_text().split('SAMPLE = """')[1].split('"""')[0]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.md"
            p.write_text(sample)
            r = subprocess.run([sys.executable, str(REPO / "doctor.py"), "--mode", "tailor", "--config", str(p)], capture_output=True, text=True)
            self.assertIn("config valid", r.stdout)


if __name__ == "__main__":
    unittest.main()
