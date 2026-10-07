import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import sheet_append
import sheet_update
import sheet_init
import jak_google


def cfg_env(tmp, text):
    p = Path(tmp) / "c.md"
    p.write_text(text)
    return mock.patch.dict(os.environ, {"JAK_CONFIG": str(p)})


STD = ["Date", "Company", "Position", "Resume Drive", "Job Nature", "Job Type", "Location",
       "Job Link", "Job Description", "Job Status", "How Applied", "Contact/Email",
       "Salary/Budget", "Deadline", "Comments"]

RENAMED = ["Date", "Employer", "Role", "CV Link", "Employment", "Workplace", "City",
           "Posting URL", "Details", "Stage", "Channel", "Recruiter",
           "Pay", "Apply By", "Notes", "Internal ID"]


class MappingTests(unittest.TestCase):
    def test_standard_headers_map_in_order(self):
        m = sheet_append.column_map_from_header(STD)
        self.assertEqual(m["date"], 0)
        self.assertEqual(m["job_desc"], 8)
        self.assertEqual(m["comments"], 14)

    def test_renamed_reordered_with_extras(self):
        m = sheet_append.column_map_from_header(RENAMED)
        self.assertEqual(len(m), 15)
        self.assertEqual(RENAMED[m["company"]], "Employer")
        self.assertEqual(RENAMED[m["position"]], "Role")
        self.assertEqual(RENAMED[m["drive_link"]], "CV Link")
        self.assertEqual(RENAMED[m["job_link"]], "Posting URL")
        self.assertEqual(RENAMED[m["status"]], "Stage")
        self.assertNotIn(15, set(m.values()))  # "Internal ID" untouched

    def test_missing_column_rejected(self):
        with self.assertRaises(sheet_append.RowError) as cm:
            sheet_append.column_map_from_header([h for h in STD if h != "Deadline"])
        self.assertIn("deadline", str(cm.exception))

    def test_ambiguous_column_rejected(self):
        with self.assertRaises(sheet_append.RowError):
            sheet_append.column_map_from_header(STD + ["State"])

    def test_col_letter(self):
        self.assertEqual(sheet_append.col_letter(1), "A")
        self.assertEqual(sheet_append.col_letter(15), "O")
        self.assertEqual(sheet_append.col_letter(26), "Z")
        self.assertEqual(sheet_append.col_letter(27), "AA")

    def test_build_mapped_row_places_values(self):
        m = sheet_append.column_map_from_header(RENAMED)
        row = sheet_append.build_mapped_row({"company": "Acme", "status": "Found"}, m, len(RENAMED))
        self.assertEqual(len(row), 16)
        self.assertEqual(row[m["company"]], "Acme")
        self.assertEqual(row[m["status"]], "Found")
        self.assertEqual(row[15], "")


class AdoptedAppendTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg_text = ("## Google\n- **sheet_id:** " + "s" * 20 + "\n- **sheet_tab:** Sheet1\n"
                         "- **sheet_columns:** " + json.dumps(RENAMED) + "\n")
        self.env = cfg_env(self.tmp.name, self.cfg_text)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_append_places_values_at_matched_positions(self):
        m = sheet_append.column_map_from_header(RENAMED)
        with mock.patch.object(jak_google, "sheet_get", return_value=[RENAMED]), \
             mock.patch.object(jak_google, "sheet_append", return_value={"range": "Sheet1!A2:P2"}) as a:
            res = sheet_append.append({"company": "Acme", "position": "Dev"})
        rng, rows = a.call_args[0][1], a.call_args[0][2]
        self.assertEqual(rng, "Sheet1!A:P")
        self.assertEqual(rows[0][m["company"]], "Acme")
        self.assertEqual(rows[0][m["position"]], "Dev")
        self.assertEqual(res["row_cells"], 16)

    def test_append_aborts_when_header_drifts(self):
        drifted = RENAMED + ["New Col"]
        with mock.patch.object(jak_google, "sheet_get", return_value=[drifted]), \
             mock.patch.object(jak_google, "sheet_append") as a:
            with self.assertRaises(sheet_append.RowError):
                sheet_append.append({"company": "Acme"})
        a.assert_not_called()

    def test_arrays_rejected_for_adopted_sheets(self):
        with mock.patch.object(jak_google, "sheet_get", return_value=[RENAMED]), \
             mock.patch.object(jak_google, "sheet_append") as a:
            with self.assertRaises(sheet_append.RowError):
                sheet_append.append(["x"] * 15)
        a.assert_not_called()


class UpdateFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg_text = ("## Google\n- **sheet_id:** " + "s" * 20 + "\n- **sheet_tab:** Sheet1\n")
        self.env = cfg_env(self.tmp.name, self.cfg_text)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def header_get(self, *a, **k):
        return [STD]

    def test_find_matches_company_position(self):
        rows = [["", "Acme", "Dev", "", "", "", "", "http://x", "jd", "Found", "", "", "", "", ""],
                ["", "Beta", "Dev", "", "", "", "", "", "", "", "", "", "", "", ""]]
        with mock.patch.object(jak_google, "sheet_get", side_effect=[[STD], rows]):
            hits = sheet_update.find("acme", "DEV")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["row"], 2)
        self.assertEqual(hits[0]["status"], "Found")

    def test_set_moves_pipeline_status(self):
        cur = [["", "Acme", "Dev", "", "", "", "", "", "", "Found", "", "", "", "", ""]]
        with mock.patch.object(jak_google, "sheet_get", side_effect=[[STD], cur]), \
             mock.patch.object(jak_google, "sheet_update", return_value={"range": "x"}) as u:
            out = sheet_update.set_cells(2, {"status": "Drafted", "comments": "draft r_1"})
        ranges = [w["range"] for w in out["writes"]]
        self.assertIn("Sheet1!J2", ranges)
        self.assertIn("Sheet1!O2", ranges)
        self.assertEqual(u.call_count, 2)

    def test_set_refuses_hand_set_status_without_force(self):
        cur = [["", "Acme", "Dev", "", "", "", "", "", "", "sent", "", "", "", "", ""]]
        with mock.patch.object(jak_google, "sheet_get", side_effect=[[STD], cur]), \
             mock.patch.object(jak_google, "sheet_update") as u:
            with self.assertRaises(sheet_update.UpdateError):
                sheet_update.set_cells(2, {"status": "Drafted"})
        u.assert_not_called()
        with mock.patch.object(jak_google, "sheet_get", side_effect=[[STD], cur]), \
             mock.patch.object(jak_google, "sheet_update", return_value={"range": "x"}) as u:
            sheet_update.set_cells(2, {"status": "Drafted"}, force=True)
        u.assert_called_once()

    def test_set_unknown_key_rejected(self):
        with mock.patch.object(jak_google, "sheet_get", return_value=[STD]), \
             mock.patch.object(jak_google, "sheet_update") as u:
            with self.assertRaises(sheet_update.UpdateError):
                sheet_update.set_cells(2, {"jd": "typo"})
        u.assert_not_called()


class SheetIdParseTests(unittest.TestCase):
    def test_url_and_bare_id(self):
        self.assertEqual(sheet_init.sheet_id_from(
            "https://docs.google.com/spreadsheets/d/ABC123xyz_-/edit#gid=0"), "ABC123xyz_-")
        self.assertEqual(sheet_init.sheet_id_from("ABC123xyz_-"), "ABC123xyz_-")

    def test_resolve_prefers_id_then_url(self):
        import jak_config
        url = "https://docs.google.com/spreadsheets/d/ABC123xyz_-/edit#gid=0"
        c = jak_config.Config(jak_config.parse(f"## Google\n- **sheet_url:** {url}\n"))
        self.assertEqual(sheet_append.resolve_sheet_id(c), "ABC123xyz_-")
        c = jak_config.Config(jak_config.parse("## Google\n- **sheet_id:** REALID123456789012\n"
                                               f"- **sheet_url:** {url}\n"))
        self.assertEqual(sheet_append.resolve_sheet_id(c), "REALID123456789012")
        c = jak_config.Config(jak_config.parse("## Google\n"))
        self.assertIsNone(sheet_append.resolve_sheet_id(c))

    def test_check_warns_only_when_both_missing(self):
        import jak_config
        _, w = jak_config.Config(jak_config.parse("## Google\n")).check()
        self.assertTrue(any("sheet_id" in x for x in w))
        url = "https://docs.google.com/spreadsheets/d/ABC123xyz_-/edit"
        _, w = jak_config.Config(jak_config.parse(f"## Google\n- **sheet_url:** {url}\n")).check()
        self.assertFalse(any("sheet_id" in x for x in w))


class BackendUpdateTests(unittest.TestCase):
    def tearDown(self):
        jak_google._backend = None

    def test_update_rejects_non_arrays(self):
        jak_google._backend = mock.Mock()
        for bad in ("x", ["a"], [], {"a": 1}):
            with self.assertRaises(jak_google.GoogleError):
                jak_google.sheet_update("s", "A1", bad)

    def test_update_dispatches_to_backend(self):
        fake = mock.Mock()
        fake.sheet_update.return_value = {"range": "Sheet1!J2"}
        jak_google._backend = fake
        out = jak_google.sheet_update("s", "Sheet1!J2", [["Drafted"]])
        self.assertEqual(out["range"], "Sheet1!J2")
        fake.sheet_update.assert_called_once_with("s", "Sheet1!J2", [["Drafted"]])


if __name__ == "__main__":
    unittest.main()
