import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("alert_email", Path(__file__).parents[1] / "scripts/alert_email.py")
mail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mail)


class AlertEmailTests(unittest.TestCase):
    def test_nested_triage_details_and_partial_recovery(self):
        subject, plain, rich = mail.render({"event": "recovery", "cluster": "pi-k3s", "context": {"nodes_recovered": "", "details": {"nodes_recovered": "pi5d08", "nodes_down_current": "pi5d07"}}, "timestamp": "2026-10-04T20:08:26Z"})
        self.assertIn("pi5d08", subject)
        self.assertIn("Still down: pi5d07", plain)
        self.assertIn("04:08:26 PM EDT", plain)
        self.assertIn("#a32323", rich)

    def test_html_escaped_and_headers_safe(self):
        subject, plain, rich = mail.render({"event": "incident", "summary": "<script>bad</script>", "nodes_down": "node\r\ninjected"})
        self.assertNotIn("\n", subject)
        self.assertNotIn("<script>", rich)
        self.assertIn("&lt;script&gt;", rich)
        self.assertNotIn("Payload:", plain)

    def test_naive_timestamp_is_utc_and_winter_is_est(self):
        _, plain, _ = mail.render({"timestamp": "2026-01-01T15:00:00"})
        self.assertIn("10:00:00 AM EST", plain)

    def test_direct_payload_full_recovery(self):
        _, plain, rich = mail.render({"event": "recovery", "nodes_recovered": "pi5d08", "nodes_down_current": ""})
        self.assertIn("Still down: None", plain)
        self.assertIn("#147d40", rich)

    def test_empty_and_duplicate_payload_do_not_contact_smtp(self):
        for payload in ("{}", '{"resource_type":"node","status":"node-down"}'):
            with patch.dict(os.environ, {"PAYLOAD": payload, "ALERT_STAGE": "triaged"}, clear=True), patch.object(mail.smtplib, "SMTP_SSL") as smtp:
                mail.main()
                smtp.assert_not_called()

    def test_dry_run_never_contacts_smtp(self):
        with patch.dict(os.environ, {"PAYLOAD": '{"event":"incident","nodes_down":"pi5"}', "DRY_RUN": "true"}, clear=True), patch.object(mail.smtplib, "SMTP_SSL") as smtp:
            mail.main()
            smtp.assert_not_called()


if __name__ == "__main__":
    unittest.main()
