import unittest
import json
import os
import shutil
from step6.graph_builder import GraphBuilder
from step6.entity_matcher import match_entities
from step6.schemas import ProcessingEntity

class TestStep6(unittest.TestCase):
    def setUp(self):
        self.step3_path = "tests/mock_step3"
        self.step5_path = "tests/mock_step5"
        os.makedirs(self.step3_path, exist_ok=True)
        os.makedirs(self.step5_path, exist_ok=True)
        
    def tearDown(self):
        shutil.rmtree(self.step3_path, ignore_errors=True)
        shutil.rmtree(self.step5_path, ignore_errors=True)
        
    def test_missing_prerequisite_error(self):
        builder = GraphBuilder(self.step3_path, self.step5_path)
        with self.assertRaises(FileNotFoundError) as context:
            builder.build_observed()
        self.assertIn("Missing technical prerequisite", str(context.exception))
        
    def test_cookie_evidence_cross_section(self):
        # Create fake hosts
        with open(os.path.join(self.step3_path, "hosts.json"), "w") as f:
            json.dump([], f)
            
        # Create policy facts with cookies in third_parties but not cookie_disclosures
        policy = {
            "cookie_disclosures": [{"status": "not_found", "snippet": ""}],
            "third_parties": [{"status": "extracted", "snippet": "We use cookies to track you."}]
        }
        with open(os.path.join(self.step5_path, "policy_facts.json"), "w") as f:
            json.dump(policy, f)
            
        builder = GraphBuilder(self.step3_path, self.step5_path)
        doc = builder.build_documented()
        services = [d.service for d in doc]
        self.assertIn("Cookies and Trackers", services)
        
    def test_empty_subprocessor_list(self):
        with open(os.path.join(self.step3_path, "hosts.json"), "w") as f:
            json.dump([], f)
            
        policy = {"third_parties": [{"status": "extracted", "snippet": "Check our subprocessors."}]}
        with open(os.path.join(self.step5_path, "policy_facts.json"), "w") as f:
            json.dump(policy, f)
            
        with open(os.path.join(self.step5_path, "subprocessors.json"), "w") as f:
            json.dump([], f)
            
        builder = GraphBuilder(self.step3_path, self.step5_path)
        doc = builder.build_documented()
        services = [d.service for d in doc]
        self.assertIn("Subprocessors", services) # Unresolved Reference
        self.assertNotIn("Subprocessing", services) # No actual subprocessor
        
    def test_similar_vendor_names_ambiguity(self):
        obs = [ProcessingEntity(vendor="Microsoft", service="Clarity", source="obs", purpose="Tracking")]
        doc = [ProcessingEntity(vendor="Microsoft", service="Azure OpenAI", source="doc", purpose="AI")]
        
        res = match_entities(obs, doc)
        self.assertEqual(res[0]['match_type'], 'ambiguous')
        self.assertEqual(res[0]['match_reason'], 'Vendor matches but service differs or is unspecified.')

    def test_cookie_tracker_reconciliation(self):
        obs = [ProcessingEntity(vendor="Google", service="Analytics", category="Behavioural analytics", source="obs")]
        doc = [ProcessingEntity(vendor="Broad Category", service="Cookies and Trackers", category="Tracking", source="doc")]
        res = match_entities(obs, doc)
        self.assertEqual(res[0]["match_type"], "partial_match")
        self.assertEqual(res[0]["match_reason"], "Cookie/Tracker disclosure covers observed analytics or advertising.")

if __name__ == "__main__":
    unittest.main()
