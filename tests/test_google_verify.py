import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import google_verify
import jak_google
import sheet_init


def cfg_env(tmp, text):
    p = Path(tmp) / "c.md"
    p.write_text(text)
    return mock.patch.dict(os.environ, {"JAK_CONFIG": str(p)})


class FakeBackend:
    name = "fake"

    def __init__(self, fail=None):
        self.fail = fail or set()

    def usable(self):
        return True

    def gmail_list(self, limit=3):
        if "gmail" in self.fail:
            raise jak_google.GoogleError("gmail denied: missing scope")
        return [{"id": f"m{i}", "subject": f"Subject {i}"} for i in range(limit)]

    def drive_list(self, limit=3, query=""):
        if "drive" in self.fail:
            raise jak_google.GoogleError("drive denied")
        if "spreadsheet" in query:
            return [{"id": "s1", "name": "Application Tracker", "mimeType": "sheet"}]
        return [{"id": f"f{i}", "name": f"file{i}.pdf", "mimeType": "pdf"} for i in range(limit)]


class VerifyTests(unittest.TestCase):
    def tearDown(self):
        jak_google._backend = None

    def test_all_ok(self):
        jak_google._backend = FakeBackend()
        rep = google_verify.verify(3)
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["backend"], "fake")
        self.assertEqual(len(rep["checks"]["gmail"]["messages"]), 3)
        self.assertEqual(len(rep["checks"]["drive"]["files"]), 3)
        self.assertEqual(rep["checks"]["sheets"]["sheets"][0]["name"], "Application Tracker")

    def test_partial_failure_reported(self):
        jak_google._backend = FakeBackend(fail={"gmail"})
        rep = google_verify.verify(3)
        self.assertFalse(rep["ok"])
        self.assertFalse(rep["checks"]["gmail"]["ok"])
        self.assertIn("scope", rep["checks"]["gmail"]["error"])
        self.assertTrue(rep["checks"]["drive"]["ok"])

    def test_no_backend_reports_cleanly(self):
        jak_google._backend = None
        with cfg_env(tempfile.mkdtemp(), "## Google\n- **google_backend:** bogus\n"):
            rep = google_verify.verify(3)
        self.assertFalse(rep["ok"])
        self.assertFalse(rep["checks"]["backend"]["ok"])


class AdoptFolderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = cfg_env(self.tmp.name, "## Google\n")
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_folder_id_from_url_and_bare(self):
        self.assertEqual(sheet_init.folder_id_from(
            "https://drive.google.com/drive/folders/ABC123xyz_-"), "ABC123xyz_-")
        self.assertEqual(sheet_init.folder_id_from("ABC123xyz_-"), "ABC123xyz_-")

    def test_adopt_folder_writes_config(self):
        code = sheet_init.adopt_folder("https://drive.google.com/drive/folders/ABC123xyz_-", False)
        self.assertEqual(code, 0)
        import jak_config
        cfg = jak_config.load()
        self.assertEqual(cfg.get("drive_folder_id"), "ABC123xyz_-")


if __name__ == "__main__":
    unittest.main()
