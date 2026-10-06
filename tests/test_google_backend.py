import os, stat, tempfile, unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import jak_google


class Fake:
    name = "fake"

    def __init__(self, parents=None):
        self.parents = parents or []
        self.shared = []
        self.drafts = []

    def usable(self): return True
    def drive_parents(self, fid): return self.parents
    def drive_share_anyone(self, fid): self.shared.append(fid)
    def draft(self, *a): self.drafts.append(a); return {"draft_id": "d1"}
    def drive_upload(self, path, name, parent): return {"id": "f1", "link": "l"}


def cfg_env(tmp, text):
    p = Path(tmp) / "c.md"
    p.write_text(text)
    return mock.patch.dict(os.environ, {"JAK_CONFIG": str(p)})


class ShareGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        jak_google._backend = None
        self.tmp.cleanup()

    def test_refused_when_no_folder_configured(self):
        fake = Fake(parents=["p"])
        jak_google._backend = fake
        with cfg_env(self.tmp.name, "## Google\n- **google_backend:** auto\n"):
            with self.assertRaises(jak_google.GoogleError):
                jak_google.share_anyone("f1")
        self.assertEqual(fake.shared, [])

    def test_refused_outside_configured_folder(self):
        fake = Fake(parents=["other"])
        jak_google._backend = fake
        with cfg_env(self.tmp.name, "## Google\n- **drive_folder_id:** FOLDER123456789012345\n"):
            with self.assertRaises(jak_google.GoogleError):
                jak_google.share_anyone("f1")
        self.assertEqual(fake.shared, [])

    def test_allowed_inside_folder_or_templates_folder(self):
        for parent in ("FOLDER123456789012345", "TEMPL1234567890123456"):
            fake = Fake(parents=[parent])
            jak_google._backend = fake
            with cfg_env(self.tmp.name, "## Google\n- **drive_folder_id:** FOLDER123456789012345\n- **drive_templates_folder_id:** TEMPL1234567890123456\n"):
                self.assertEqual(jak_google.share_anyone("f1")["shared"], "anyone-reader")
            self.assertEqual(fake.shared, ["f1"])

    def test_upload_shares_only_after_guard(self):
        pdf = Path(self.tmp.name) / "a.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        fake = Fake(parents=["FOLDER123456789012345"])
        jak_google._backend = fake
        with cfg_env(self.tmp.name, "## Google\n- **drive_folder_id:** FOLDER123456789012345\n"):
            res = jak_google.drive_upload(str(pdf))
        self.assertEqual(res["shared"], "anyone-reader")

    def test_missing_attachment_rejected_before_backend(self):
        fake = Fake()
        jak_google._backend = fake
        with self.assertRaises(jak_google.GoogleError):
            jak_google.draft("a@b.c", "s", "b", ["/nonexistent.pdf"])
        self.assertEqual(fake.drafts, [])

    def test_sheet_append_requires_array_of_arrays(self):
        jak_google._backend = Fake()
        for bad in ("x", ["a"], [], {"a": 1}):
            with self.assertRaises(jak_google.GoogleError):
                jak_google.sheet_append("s", "A:O", bad)


class BackendSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        jak_google._backend = None

    def tearDown(self):
        jak_google._backend = None
        self.tmp.cleanup()

    def fake_gog(self, ok: bool) -> str:
        p = Path(self.tmp.name) / "gog"
        p.write_text("#!/usr/bin/env bash\nexit %d\n" % (0 if ok else 1))
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
        return str(p)

    def env(self, extra=None, cfg="## Google\n- **google_backend:** auto\n"):
        c = Path(self.tmp.name) / "c.md"
        c.write_text(cfg)
        base = {"JAK_CONFIG": str(c), "JAK_GOOGLE_DIR": str(Path(self.tmp.name) / "g")}
        base.update(extra or {})
        return mock.patch.dict(os.environ, base)

    def test_auto_prefers_gog_when_it_unlocks(self):
        with self.env({"JAK_GOG_BIN": self.fake_gog(True)}):
            self.assertEqual(jak_google.backend().name, "gog")

    def test_auto_falls_back_to_python_when_gog_locked(self):
        g = Path(self.tmp.name) / "g"
        g.mkdir()
        (g / "google_token_default.json").write_text("{}")
        with self.env({"JAK_GOG_BIN": self.fake_gog(False), "JAK_GOOGLE_ACCOUNT": "default"}):
            self.assertEqual(jak_google.backend().name, "python")

    def test_error_when_nothing_usable(self):
        with self.env({"JAK_GOG_BIN": self.fake_gog(False)}):
            with self.assertRaises(jak_google.GoogleError) as cm:
                jak_google.backend()
        self.assertIn("no usable Google backend", str(cm.exception))

    def test_access_token_env_counts_as_usable_gog(self):
        with self.env({"JAK_GOG_BIN": self.fake_gog(False), "GOG_ACCESS_TOKEN": "x"}):
            self.assertEqual(jak_google.backend().name, "gog")

    def test_invalid_backend_value(self):
        with self.env(cfg="## Google\n- **google_backend:** bogus\n"):
            with self.assertRaises(jak_google.GoogleError):
                jak_google.backend()


if __name__ == "__main__":
    unittest.main()
