import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = str(REPO / "skills" / "job-apply-core" / "scripts" / "cv_fetch.py")

sys.path.insert(0, str(REPO / "skills" / "job-apply-core" / "scripts"))
import cv_fetch


class CvFetchTests(unittest.TestCase):
    def test_google_docs_needs_debug_browser(self):
        plan = cv_fetch.classify("https://docs.google.com/document/d/1AbC12xYz_qWERTY/edit?usp=sharing")
        self.assertEqual(plan["kind"], "google-docs")
        self.assertEqual(plan["method"], "debug-browser")
        self.assertEqual(plan["doc_id"], "1AbC12xYz_qWERTY")
        self.assertEqual(plan["mobile_url"], "https://docs.google.com/document/d/1AbC12xYz_qWERTY/mobilebasic")
        self.assertEqual(plan["export_txt_url"], "https://docs.google.com/document/d/1AbC12xYz_qWERTY/export?format=txt")

    def test_mobilebasic_input_classifies_same_doc(self):
        plan = cv_fetch.classify("https://docs.google.com/document/d/1AbC12xYz_qWERTY/mobilebasic")
        self.assertEqual(plan["kind"], "google-docs")
        self.assertEqual(plan["doc_id"], "1AbC12xYz_qWERTY")
        self.assertEqual(plan["mobile_url"], "https://docs.google.com/document/d/1AbC12xYz_qWERTY/mobilebasic")

    def test_google_drive_file_needs_debug_browser(self):
        for url in ("https://drive.google.com/file/d/1AbC12xYz_qWERTY/view",
                    "https://drive.google.com/open?id=1AbC12xYz_qWERTY"):
            plan = cv_fetch.classify(url)
            self.assertEqual(plan["kind"], "google-drive-file", url)
            self.assertEqual(plan["method"], "debug-browser")

    def test_published_doc_is_plain_web(self):
        plan = cv_fetch.classify("https://docs.google.com/document/d/e/2PACX-abc/pub")
        self.assertEqual(plan["kind"], "web")

    def test_plain_url_is_webfetch_with_verify(self):
        plan = cv_fetch.classify("https://example.com/my-cv.html")
        self.assertEqual(plan["kind"], "web")
        self.assertIn("FULL", plan["detail"])

    def test_local_pdf_and_text(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            pdf = Path(t) / "cv.pdf"
            pdf.write_bytes(b"%PDF-1.4 fake")
            self.assertEqual(cv_fetch.classify(str(pdf))["method"], "pdf")
            txt = Path(t) / "cv.md"
            txt.write_text("hi")
            self.assertEqual(cv_fetch.classify(str(txt))["method"], "read")

    def test_missing_path_and_empty_are_unknown(self):
        self.assertEqual(cv_fetch.classify("/no/such/file.pdf")["kind"], "unknown")
        self.assertEqual(cv_fetch.classify("   ")["kind"], "unknown")

    def test_cli_json_and_exit_codes(self):
        r = subprocess.run([sys.executable, SCRIPT, "--json-only", "https://docs.google.com/document/d/ABC123/edit"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["kind"], "google-docs")
        r = subprocess.run([sys.executable, SCRIPT, ""], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
