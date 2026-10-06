"""Importing a pipeline script must never require a config file to already exist — only calling its
functions should. A module-level `bc.REPO` / `L.REPO` access (or any other config-backed lazy
attribute) breaks --help, static analysis, and any future test tooling that just imports the module.

This caught two real bugs (2026-10-06): `bd3_filter_apply.py` and `li3_apply.py` both aliased
`bc.REPO`/`L.REPO` into a module-level constant, which eagerly loaded the config at import time."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths
from _paths import REPO

SCRIPT_DIRS = [
    REPO / "skills" / "bdjobs-full-run" / "scripts",
    REPO / "skills" / "li-full-run" / "scripts",
    REPO / "skills" / "check-discord-jobs" / "scripts",
]
# CLI-only scripts that read sys.argv at module level by design (never meant to be imported as a library)
NOT_IMPORTABLE = {"type_salary"}


class ImportWithoutConfigTests(unittest.TestCase):
    def test_every_script_imports_with_no_config_present(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, JAK_CONFIG=str(Path(d) / "does-not-exist.md"))
            for script_dir in SCRIPT_DIRS:
                for f in script_dir.glob("*.py"):
                    name = f.stem
                    if name in NOT_IMPORTABLE:
                        continue
                    r = subprocess.run([sys.executable, "-c", f"import {name}"], capture_output=True,
                                       text=True, cwd=str(script_dir), env=env)
                    self.assertEqual(r.returncode, 0, f"{f}: {r.stderr[-500:]}")

    def test_no_review_posts_script(self):
        # review_posts.py was a one-off, unreferenced, hardcoded-date script that ran a full pass as
        # an import side effect (no `if __name__` guard at all). Dropped entirely (2026-10-06); this
        # guards against it, or something like it, being re-added.
        self.assertFalse((REPO / "skills" / "li-full-run" / "scripts" / "review_posts.py").exists())


if __name__ == "__main__":
    unittest.main()
