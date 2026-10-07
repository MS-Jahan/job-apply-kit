import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO))
import install as installer


def git(*args, cwd, env=None):
    e = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_NOGLOBAL="1",
             GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
             GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    if env:
        e.update(env)
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, env=e)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        git("init", "-q", cwd=self.t)
        (self.t / "f.txt").write_text("x")
        git("add", ".", cwd=self.t)
        git("commit", "-qm", "init", cwd=self.t)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_repo_reports_not_dirty(self):
        is_repo, dirty = installer.git_status(self.t)
        self.assertTrue(is_repo)
        self.assertEqual(dirty, [])

    def test_dirty_repo_lists_changes(self):
        (self.t / "f.txt").write_text("changed")
        (self.t / "new.txt").write_text("new")
        is_repo, dirty = installer.git_status(self.t)
        self.assertTrue(is_repo)
        blob = "\n".join(dirty)
        self.assertIn("f.txt", blob)
        self.assertIn("new.txt", blob)

    def test_non_repo_detected(self):
        with tempfile.TemporaryDirectory() as d:
            is_repo, dirty = installer.git_status(Path(d))
        self.assertFalse(is_repo)
        self.assertEqual(dirty, [])

    def test_git_update_refuses_dirty_checkout(self):
        (self.t / "f.txt").write_text("changed")
        # Point the updater at the temp repo by monkeypatching REPO.
        old = installer.REPO
        installer.REPO = self.t
        try:
            rc = installer.git_update(dry=True)
        finally:
            installer.REPO = old
        self.assertNotEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
