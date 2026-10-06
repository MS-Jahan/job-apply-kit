import re, unittest
from pathlib import Path

import _paths
from _paths import REPO

SEND_PATTERNS = [
    r"\.messages\(\)\.send\(",
    r"\.drafts\(\)\.send\(",
    r"""["']drafts["']\s*,\s*["']send["']""",
    r"""["']gmail["']\s*,\s*["'](send|reply)["']""",
    r"gmail\s+(send|reply)\b",
    r"gmail\.send",
]


def code_files():
    for p in REPO.rglob("*"):
        if p.suffix in (".py", ".sh") and "__pycache__" not in p.parts and ".git" not in p.parts and "tests" not in p.relative_to(REPO).parts:
            yield p


class NeverSubmitTests(unittest.TestCase):
    def test_no_mail_send_code_anywhere(self):
        hits = []
        for p in code_files():
            text = p.read_text(encoding="utf-8", errors="replace")
            for pat in SEND_PATTERNS:
                for m in re.finditer(pat, text):
                    line = text.count("\n", 0, m.start()) + 1
                    # allow the documentation lines that state the prohibition
                    if "never" in text.splitlines()[line - 1].lower() or "NOT" in text.splitlines()[line - 1] or "deliberately" in text.splitlines()[line - 1].lower():
                        continue
                    hits.append(f"{p.relative_to(REPO)}:{line}: {m.group(0)}")
        self.assertEqual(hits, [], "mail send path found")

    def test_operations_states_the_invariants(self):
        text = (REPO / "skills/job-apply-core/OPERATIONS.md").read_text()
        self.assertIn("**Never submit.**", text)
        self.assertIn("**Never send.**", text)
        self.assertIn("No script in this kit can send mail", text)


if __name__ == "__main__":
    unittest.main()
