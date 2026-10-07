import os, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "skills" / "job-apply-core" / "scripts"))
import jak_config  # noqa: E402

SAMPLE = """# cfg
## Identity
- **name:** Ada Example
- **name_file:** Ada_Example
- **phone:** +15551234567
- **email_header:** ada@example.org
- **email_google:** ada.g@example.com
## Sources
- **cv_source:** https://example.org/cv, https://example.org/resume
## Truth gates
- **banned_claims:** Kubernetes, Kafka
- **unproven_claims:**
## Signature
- **email_signature:** Best regards,
    Ada Example
    ada@example.org
Some prose line that is not a key.
## Browser
- **cdp_port:** 9333
"""


class ConfigTests(unittest.TestCase):
    def cfg(self, text=SAMPLE):
        return jak_config.Config(jak_config.parse(text))

    def test_parse_and_lists(self):
        c = self.cfg()
        self.assertEqual(c.get("name"), "Ada Example")
        self.assertEqual(c.list("cv_source"), ["https://example.org/cv", "https://example.org/resume"])
        self.assertEqual(c.list("banned_claims"), ["Kubernetes", "Kafka"])
        self.assertEqual(c.list("unproven_claims"), [])
        self.assertEqual(c.int("cdp_port"), 9333)

    def test_multiline_value(self):
        self.assertEqual(self.cfg().get("email_signature").splitlines(), ["Best regards,", "Ada Example", "ada@example.org"])

    def test_placeholder_is_unset(self):
        c = self.cfg("## Identity\n- **name:** <Your Full Name>\n")
        self.assertFalse(c.get("name"))

    def test_defaults(self):
        c = self.cfg()
        self.assertEqual(c.get("default_doc"), "resume")
        self.assertEqual(c.get("google_backend"), "auto")
        self.assertTrue(c.bool("template_default"))
        self.assertTrue(str(c.path("templates_dir")).endswith("templates"))

    def test_check_names_missing_key(self):
        errors, _ = self.cfg("## Identity\n- **name:** X\n").check()
        self.assertTrue(any("name_file" in e for e in errors))
        self.assertTrue(any("cv_source" in e for e in errors))

    def test_check_ok(self):
        errors, _ = self.cfg().check()
        self.assertEqual(errors, [])

    def test_bad_values_fail(self):
        errors, _ = self.cfg(SAMPLE + "- **sheet_id:** short\n").check()
        self.assertTrue(any("sheet_id" in e for e in errors))
        errors, _ = self.cfg(SAMPLE.replace("9333", "abc")).check()
        self.assertTrue(any("cdp_port" in e for e in errors))

    def test_mask(self):
        self.assertNotIn("1234567", jak_config.mask("phone", "+15551234567"))
        self.assertNotIn("ada@example.org", jak_config.mask("email_header", "ada@example.org"))
        self.assertEqual(jak_config.mask("name", "Ada Example"), "Ada Example")

    def test_example_config_has_all_required_keys_but_unset(self):
        text = (REPO / "config.example.md").read_text()
        c = jak_config.Config(jak_config.parse(text))
        errors, _ = c.check()
        # placeholders are unset, so required-key errors are expected, and nothing else
        self.assertTrue(all(e.startswith("missing required key") for e in errors), errors)
        for k in jak_config.REQUIRED:
            self.assertIn("**%s:**" % k, text)

    def test_cli_check_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.md"
            p.write_text(SAMPLE)
            self.assertEqual(jak_config.main(["--config", str(p), "--check"]), 0)
            p.write_text("## Identity\n- **name:** X\n")
            self.assertEqual(jak_config.main(["--config", str(p), "--check"]), 1)
            self.assertEqual(jak_config.main(["--config", str(Path(d) / "nope.md"), "--check"]), 1)

    def test_sync_keys_adds_missing_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.md"
            p.write_text("## Identity\n- **name:** Ada\n- **cdp_port:** 9333\n")
            added = jak_config.sync_keys(p)
            self.assertIn("discord_channels", added)
            self.assertIn("sheet_url", added)
            self.assertNotIn("name", added)
            self.assertNotIn("cdp_port", added)
            text = p.read_text()
            self.assertIn("- **name:** Ada", text)
            self.assertIn("- **cdp_port:** 9333", text)
            cfg = jak_config.Config(jak_config.parse(text))
            self.assertEqual(cfg.get("name"), "Ada")
            self.assertIsNone(cfg.get("discord_channels"))
            self.assertEqual(jak_config.sync_keys(p), [])

    def test_need_gate_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.md"
            p.write_text("## Identity\n- **name:** Ada\n")
            self.assertEqual(jak_config.main(["--config", str(p), "--need", "name"]), 0)
            self.assertEqual(jak_config.main(["--config", str(p), "--need", "sheet_id"]), 2)
            self.assertEqual(jak_config.main(["--config", str(p), "--need", "sheet_id", "--optional"]), 3)
            self.assertEqual(jak_config.main(["--config", str(p), "--need", "remote_ok"]), 0)  # has a default


if __name__ == "__main__":
    unittest.main()
