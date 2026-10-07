"""Docs (README, docs/*.md) are plain files — install.py never renders them, so they must never
contain the {{...}} skill-install tokens, and every file path they mention must actually exist."""
import re
import unittest
from pathlib import Path

import _paths
from _paths import REPO

DOC_FILES = (
    [REPO / "README.md"]
    + list((REPO / "docs").glob("*.md"))
    + list((REPO / "docs" / "help").glob("*.md"))
)


class HelpIndexTests(unittest.TestCase):
    def test_help_index_links_resolve(self):
        # docs/help/index.md is the landing page: every .md link in it and every
        # page it lists must exist, and every help page must link back to it.
        index = REPO / "docs" / "help" / "index.md"
        self.assertTrue(index.is_file())
        pages = sorted((REPO / "docs" / "help").glob("*.md"))
        self.assertGreater(len(pages), 1)
        for target in re.findall(r"\(([\w\-]+\.md)\)", index.read_text(encoding="utf-8")):
            self.assertTrue((index.parent / target).is_file(), f"index links missing {target}")
        for page in pages:
            if page.name == "index.md":
                continue
            self.assertIn("(index.md)", page.read_text(encoding="utf-8"),
                          f"{page.name} does not link back to index.md")


class DocTokenTests(unittest.TestCase):
    def test_no_unrendered_install_tokens(self):
        for f in DOC_FILES:
            text = f.read_text(encoding="utf-8")
            self.assertNotIn("{{", text, f.relative_to(REPO))

    def test_referenced_scripts_exist(self):
        for f in DOC_FILES:
            text = f.read_text(encoding="utf-8")
            for rel in re.findall(r"skills/[A-Za-z0-9_\-/.]+\.(?:py|md|sh)", text):
                self.assertTrue((REPO / rel).is_file(), f"{f.name} references missing {rel}")

    def test_readme_mentions_every_shipped_skill(self):
        # resume-kit is a pure shared-data dependency (like job-apply-core's own scripts/ references),
        # never invoked directly, so it has no row of its own in the user-facing skill index.
        internal_only = {"resume-kit"}
        text = (REPO / "README.md").read_text()
        for d in (REPO / "skills").iterdir():
            if (d / "SKILL.md").is_file() and d.name not in internal_only:
                self.assertIn(f"`{d.name}`", text, f"README is missing {d.name}")

    def test_credits_names_both_upstream_projects(self):
        text = (REPO / "docs" / "CREDITS.md").read_text()
        self.assertIn("humanizer", text.lower())
        self.assertIn("resume", text.lower())
        self.assertIn("MIT", text)

    def test_license_is_mit(self):
        text = (REPO / "LICENSE").read_text()
        self.assertIn("MIT License", text)


class ConfigDocTests(unittest.TestCase):
    def test_every_config_key_documented(self):
        # docs/help/00-config.md is the central key reference: every script-read
        # key in config.example.md must be explained there.
        example = (REPO / "config.example.md").read_text(encoding="utf-8")
        ref = (REPO / "docs" / "help" / "00-config.md").read_text(encoding="utf-8")
        keys = re.findall(r"^- \*\*([A-Za-z0-9_]+):\*\*", example, re.M)
        self.assertTrue(keys)
        for k in keys:
            self.assertIn(f"`{k}`", ref, f"00-config.md does not document {k}")


class DockerfileTests(unittest.TestCase):
    def test_dockerfile_structure(self):
        text = (REPO / "Dockerfile").read_text()
        self.assertIn("requirements.txt", text)
        self.assertIn("tectonic", text)
        self.assertIn("poppler-utils", text)
        self.assertIn("tests/run.sh", text)
        # no secrets, no browser bundled
        for bad in ("GOOGLE_", "TOKEN", "chrome", "agent-browser"):
            self.assertNotIn(bad, text)


if __name__ == "__main__":
    unittest.main()
