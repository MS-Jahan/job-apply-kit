import re, unittest
from pathlib import Path

import _paths
from _paths import REPO

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SKILLS = REPO / "skills"


def skill_dirs():
    return sorted(p for p in SKILLS.iterdir() if p.is_dir())


def frontmatter(md: Path) -> dict:
    m = re.match(r"^---\n(.*?)\n---", md.read_text(encoding="utf-8"), re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if k:
            out[k.group(1)] = k.group(2).strip().strip("'\"")
    return out


class SkillTests(unittest.TestCase):
    def test_frontmatter_valid(self):
        for d in skill_dirs():
            fm = frontmatter(d / "SKILL.md")
            self.assertEqual(fm.get("name"), d.name, d.name)
            self.assertRegex(d.name, NAME_RE)
            self.assertTrue(1 <= len(fm.get("description", "")) <= 1024, d.name)

    def test_requires_point_to_existing_skills(self):
        names = {d.name for d in skill_dirs()}
        for d in skill_dirs():
            f = d / "requires.txt"
            if f.exists():
                for line in f.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self.assertIn(line, names, f"{d.name} requires unknown {line}")

    def test_script_paths_in_markdown_exist(self):
        for d in skill_dirs():
            for md in d.rglob("*.md"):
                text = md.read_text(encoding="utf-8")
                for token, base in (("{{CORE_DIR}}", SKILLS / "job-apply-core"), ("{{SKILL_DIR}}", d)):
                    for rel in re.findall(re.escape(token) + r"/((?:scripts|references)/[A-Za-z0-9_./-]+\.(?:py|md|sh))", text):
                        self.assertTrue((base / rel).exists(), f"{md.relative_to(REPO)} references missing {token}/{rel}")

    def test_operations_anchor_links_resolve(self):
        ops = (SKILLS / "job-apply-core" / "OPERATIONS.md").read_text()
        anchors = set(re.findall(r'<a id="([a-z0-9-]+)"></a>', ops))
        self.assertTrue({"precedence", "accounts", "truth", "format", "documents", "tracking", "browser"} <= anchors)
        for md in list(SKILLS.rglob("*.md")) + list((REPO / "docs").rglob("*.md")) + [REPO / "README.md"]:
            if not md.exists():
                continue
            for a in re.findall(r"OPERATIONS\.md#([a-z0-9-]+)", md.read_text(encoding="utf-8")):
                self.assertIn(a, anchors, f"{md.relative_to(REPO)} -> OPERATIONS.md#{a}")

    def test_no_stale_source_paths(self):
        # Generic checks only. Personal values are scanned by test_no_pii with a private pattern file.
        bad = [re.compile(p) for p in (r"/home/[A-Za-z0-9_-]+/", r"JDs/bdjobs/cdp\.py", r"JDs/tracker/gmail_draft\.py")]
        for f in SKILLS.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".py", ".sh"):
                text = f.read_text(encoding="utf-8", errors="replace")
                for rx in bad:
                    self.assertIsNone(rx.search(text), f"{f.relative_to(REPO)} matches {rx.pattern}")


if __name__ == "__main__":
    unittest.main()
