import json, sys, unittest

import _paths
from _paths import REPO

sys.path.insert(0, str(REPO / "skills" / "check-discord-jobs" / "scripts"))
import scan_channel as sc  # noqa: E402


class ScanChannelTests(unittest.TestCase):
    def test_parse_extract_handles_double_encoding(self):
        data = [{"id": "1", "time": "2026-01-02T00:00:00Z"}]
        once = json.dumps(data)
        twice = json.dumps(once)
        self.assertEqual(sc.parse_extract(once), data)
        self.assertEqual(sc.parse_extract(twice), data)
        self.assertEqual(sc.parse_extract("garbage"), [])
        self.assertEqual(sc.parse_extract(json.dumps({"a": 1})), [])

    def test_oldest_date(self):
        merged = {"1": {"time": "2026-03-02T10:00:00Z"}, "2": {"time": "2026-02-01T10:00:00Z"}, "3": {}}
        self.assertEqual(sc.oldest_date(merged), "2026-02-01")
        self.assertEqual(sc.oldest_date({}), "")

    def test_embedded_scripts_are_present(self):
        self.assertIn("message-content-", sc.EXTRACT)
        self.assertIn("scrollTop", sc.SCROLL)

    def test_no_external_file_dependency(self):
        text = (REPO / "skills/check-discord-jobs/scripts/scan_channel.py").read_text()
        self.assertNotIn("/tmp/", text)


if __name__ == "__main__":
    unittest.main()
