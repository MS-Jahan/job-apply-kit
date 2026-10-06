import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALL = str(REPO / "install.py")


def run(args, env):
    return subprocess.run([sys.executable, INSTALL] + args, capture_output=True, text=True, env=env)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = Path(self.tmp.name) / "skills"
        self.env = dict(os.environ, JAK_MANIFEST=str(Path(self.tmp.name) / "manifest.json"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_install_renders_tokens_and_manifest(self):
        r = run(["--dest", str(self.dest)], self.env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        md = (self.dest / "job-apply-core" / "SKILL.md").read_text()
        self.assertNotIn("{{", md)
        self.assertIn(str(self.dest / "job-apply-core"), md)
        manifest = json.loads(Path(self.env["JAK_MANIFEST"]).read_text())
        self.assertIn(str(self.dest / "job-apply-core"), manifest)

    def test_uninstall_removes_only_manifest_entries(self):
        other = self.dest / "someone-elses-skill"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("---\nname: someone-elses-skill\ndescription: x\n---\n")
        run(["--dest", str(self.dest)], self.env)
        r = run(["--dest", str(self.dest), "--uninstall"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.dest / "job-apply-core").exists())
        self.assertTrue(other.exists())

    def test_refuses_to_overwrite_foreign_skill(self):
        foreign = self.dest / "job-apply-core"
        foreign.mkdir(parents=True)
        (foreign / "SKILL.md").write_text("---\nname: job-apply-core\ndescription: foreign\n---\n")
        r = run(["--dest", str(self.dest)], self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--force", r.stderr + r.stdout)
        r = run(["--dest", str(self.dest), "--force"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_dry_run_writes_nothing(self):
        r = run(["--dest", str(self.dest), "--dry-run"], self.env)
        self.assertEqual(r.returncode, 0)
        self.assertFalse(self.dest.exists())
        self.assertFalse(Path(self.env["JAK_MANIFEST"]).exists())

    def test_link_mode_symlinks_scripts_but_renders_markdown(self):
        run(["--dest", str(self.dest), "--link"], self.env)
        script = self.dest / "job-apply-core" / "scripts" / "jak_config.py"
        self.assertTrue(script.is_symlink())
        self.assertFalse((self.dest / "job-apply-core" / "SKILL.md").is_symlink())

    def test_every_shipped_skill_has_valid_frontmatter(self):
        r = run(["--dest", str(self.dest), "--dry-run"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
