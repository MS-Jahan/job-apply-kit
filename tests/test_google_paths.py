import os, stat, tempfile, unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import google_paths
import google_auth


class PathTests(unittest.TestCase):
    def test_lookup_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "g"
            with mock.patch.dict(os.environ, {"JAK_GOOGLE_DIR": str(d), "JAK_CONFIG": str(Path(t) / "none.md")}):
                google_paths.token_dir(); google_paths.token_path("a@b.c"); google_paths.list_accounts()
                self.assertFalse(d.exists())

    def test_ensure_dir_is_private(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "g"
            with mock.patch.dict(os.environ, {"JAK_GOOGLE_DIR": str(d), "JAK_CONFIG": str(Path(t) / "none.md")}):
                google_paths.ensure_dir()
                self.assertEqual(stat.S_IMODE(d.stat().st_mode), 0o700)

    def test_slug_and_account_files(self):
        with tempfile.TemporaryDirectory() as t:
            with mock.patch.dict(os.environ, {"JAK_GOOGLE_DIR": t, "JAK_CONFIG": str(Path(t) / "none.md")}):
                self.assertEqual(google_paths.slug("Ada.G+x@Example.com"), "ada_g_x_example_com")
                google_paths.token_path("a@b.c").write_text("{}")
                self.assertEqual(google_paths.list_accounts(), ["a_b_c"])

    def test_scopes_never_request_send(self):
        self.assertFalse([s for s in google_auth.SCOPES if s.endswith("gmail.send")])
        self.assertTrue(set(google_auth.CORE_SCOPES) <= set(google_auth.SCOPES))

    def test_missing_token_gives_actionable_error(self):
        with tempfile.TemporaryDirectory() as t:
            with mock.patch.dict(os.environ, {"JAK_GOOGLE_DIR": t, "JAK_CONFIG": str(Path(t) / "none.md")}):
                with self.assertRaises(google_auth.AuthError) as cm:
                    google_auth.credentials("nobody@example.invalid")
        self.assertIn("google_setup.py", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
