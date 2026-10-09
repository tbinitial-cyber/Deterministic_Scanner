import unittest
import os
import json
import subprocess
from step3.analyzer import IntelligenceAnalyzer
from step3.schemas import EnrichedHost

class TestStep3(unittest.TestCase):
    def setUp(self):
        self.analyzer = IntelligenceAnalyzer("https://miro.com")

    def test_db_loading_from_any_dir(self):
        orig_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(orig_cwd))
            analyzer = IntelligenceAnalyzer("https://miro.com")
            self.assertIn("clarity.ms", analyzer.db["hosts"])
        finally:
            os.chdir(orig_cwd)

    def test_known_unknown_hosts(self):
        known = self.analyzer.resolve_host("clarity.ms")
        self.assertEqual(known["vendor"], "Microsoft")

        unknown = self.analyzer.resolve_host("random-unknown-domain.com")
        self.assertEqual(unknown["vendor"], "Unknown")
        self.assertEqual(unknown["category"], "Other / Unknown")

    def test_cookie_resolution(self):
        known_cookie = self.analyzer.resolve_cookie("_ga", "google-analytics.com")
        self.assertEqual(known_cookie["vendor"], "Google")

    def test_hostname_boundaries(self):
        self.assertTrue(self.analyzer.is_first_party("miro.com"))
        self.assertTrue(self.analyzer.is_first_party("www.miro.com"))
        self.assertTrue(self.analyzer.is_first_party("miro.com."))

        self.assertFalse(self.analyzer.is_first_party("NOTMIRO.COM"))
        self.assertFalse(self.analyzer.is_first_party("miro.com.attacker.test"))
        self.assertFalse(self.analyzer.is_first_party("attacker-miro.com"))

        analyzer_uk = IntelligenceAnalyzer("https://example.co.uk")
        self.assertTrue(analyzer_uk.is_first_party("example.co.uk"))
        self.assertTrue(analyzer_uk.is_first_party("www.example.co.uk"))
        self.assertFalse(analyzer_uk.is_first_party("notexample.co.uk"))
        self.assertFalse(analyzer_uk.is_first_party("example.co.uk.attacker.com"))

        # IP and localhost tests
        analyzer_local = IntelligenceAnalyzer("http://localhost:8080")
        self.assertTrue(analyzer_local.is_first_party("localhost"))
        self.assertFalse(analyzer_local.is_first_party("127.0.0.1"))

        analyzer_ip = IntelligenceAnalyzer("http://127.0.0.1")
        self.assertTrue(analyzer_ip.is_first_party("127.0.0.1"))
        self.assertFalse(analyzer_ip.is_first_party("localhost"))

        # Malformed hostnames should be safely handled
        self.assertFalse(self.analyzer.is_first_party("invalid#hostname@!"))
        self.assertFalse(self.analyzer.is_first_party(""))

    def test_vendor_ordering_deterministic(self):
        eh1 = EnrichedHost(domain="a.com", normalized_domain="a.com", is_first_party=False, vendor="Zeta", category="X", confidence="high", consent_behavior="X")
        eh2 = EnrichedHost(domain="b.com", normalized_domain="b.com", is_first_party=False, vendor="Alpha", category="X", confidence="high", consent_behavior="X")
        eh3 = EnrichedHost(domain="c.com", normalized_domain="c.com", is_first_party=False, vendor="Beta", category="X", confidence="high", consent_behavior="X")
        enriched_hosts = [eh1, eh2, eh3]
        vendors = sorted(list({h.vendor for h in enriched_hosts if not h.is_first_party and h.vendor != "Unknown"}))
        self.assertEqual(vendors, ["Alpha", "Beta", "Zeta"])

    def test_schema_valid(self):
        eh = EnrichedHost(domain="miro.com", normalized_domain="miro.com", is_first_party=True, vendor="First", category="Cat", confidence="high", consent_behavior="pre_consent")
        self.assertEqual(eh.normalized_domain, "miro.com")

    def test_no_secrets_in_db(self):
        with open("step3/intelligence_db.json", "r", encoding="utf-8") as f:
            content = f.read().lower()
            self.assertNotIn("password", content)
            self.assertNotIn("secret", content)
            self.assertNotIn("token", content)
            # Make sure no raw miro outputs exist
            self.assertNotIn("violation", content)
            self.assertNotIn("illegal", content)

if __name__ == "__main__":
    unittest.main()
