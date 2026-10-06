import json, os, tempfile, unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import sheet_append
import jak_google


class BuildRowTests(unittest.TestCase):
    def test_object_maps_to_15_columns_in_order(self):
        row = sheet_append.build_row({"company": "Acme", "job_desc": "JD", "comments": "c"})
        self.assertEqual(len(row), 15)
        self.assertEqual(row[1], "Acme")
        self.assertEqual(row[8], "JD")
        self.assertEqual(row[14], "c")
        self.assertEqual(row[0], "")

    def test_array_must_have_15(self):
        with self.assertRaises(sheet_append.RowError):
            sheet_append.build_row(["x"] * 14)
        self.assertEqual(len(sheet_append.build_row(["x"] * 15)), 15)

    def test_unknown_key_rejected(self):
        with self.assertRaises(sheet_append.RowError):
            sheet_append.build_row({"company": "A", "jd": "typo"})

    def test_awkward_values_kept_literally(self):
        jd = "=SUM(1,2) | a, b\nline2"
        row = sheet_append.build_row({"job_desc": jd, "contact": "+880 1711-000000", "salary": None})
        self.assertEqual(row[8], jd)
        self.assertEqual(row[11], "+880 1711-000000")
        self.assertEqual(row[12], "")

    def test_columns_and_headers_aligned(self):
        self.assertEqual(len(sheet_append.COLUMNS), 15)
        self.assertEqual(len(sheet_append.HEADERS), 15)
        self.assertEqual(sheet_append.COLUMNS[8], "job_desc")  # column I
        self.assertEqual(sheet_append.COLUMNS[14], "comments")  # column O


class AppendGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        cfg = Path(self.tmp.name) / "c.md"
        cfg.write_text("## Google\n- **sheet_id:** abcdefghijklmnopqrstuvwxyz123456\n- **sheet_tab:** Sheet1\n")
        self.env = mock.patch.dict(os.environ, {"JAK_CONFIG": str(cfg)})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_dry_run_calls_nothing(self):
        with mock.patch.object(jak_google, "sheet_get") as g, mock.patch.object(jak_google, "sheet_append") as a:
            out = sheet_append.append({"company": "A"}, dry_run=True)
        g.assert_not_called(); a.assert_not_called()
        self.assertEqual(len(out["values"][0]), 15)

    def test_wrong_header_width_aborts_before_writing(self):
        with mock.patch.object(jak_google, "sheet_get", return_value=[["a"] * 14]), \
             mock.patch.object(jak_google, "sheet_append") as a:
            with self.assertRaises(sheet_append.RowError):
                sheet_append.append({"company": "A"})
        a.assert_not_called()

    def test_good_header_appends_one_15_value_row(self):
        with mock.patch.object(jak_google, "sheet_get", return_value=[["h"] * 15]), \
             mock.patch.object(jak_google, "sheet_append", return_value={"range": "Sheet1!A2:O2"}) as a:
            res = sheet_append.append({"company": "A", "job_desc": "=x"})
        args = a.call_args[0]
        self.assertEqual(args[1], "Sheet1!A:O")
        self.assertEqual(len(args[2]), 1)
        self.assertEqual(len(args[2][0]), 15)
        self.assertEqual(res["range"], "Sheet1!A2:O2")


if __name__ == "__main__":
    unittest.main()
