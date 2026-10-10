import unittest
import json
import os
import shutil
from step8.schemas import ProcessingActivity, VendorRecord
from step8.evidence_resolver import EvidenceResolver
from step8.activity_builder import ActivityBuilder
from step8.activity_grouping import group_activities

class TestStep8(unittest.TestCase):
    def setUp(self):
        # Setup synthetic inputs for testing EvidenceResolver and ActivityBuilder directly
        self.step2_consent = [
            {
                "target": "c.clarity.ms",
                "pre_consent": True,
                "accept_all": True,
                "reject_all": True,
                "classification": "present_across_states"
            },
            {
                "target": "n.clarity.ms",
                "pre_consent": False,
                "accept_all": False,
                "reject_all": True,
                "classification": "reject_only" # attempted reject all, failed
            }
        ]
        self.step6_graph = [
            {
                "match_type": "ambiguous",
                "observed": {"vendor": "Microsoft", "service": "Clarity", "purpose": "Analytics"},
                "documented": {"vendor": "Microsoft", "service": "Azure OpenAI", "purpose": "AI"},
                "confidence": "medium"
            }
        ]
        self.step6_disc = [
            {
                "type": "ambiguous_processing_entity",
                "status": "ambiguous_processing_entity",
                "observed_entity": {"vendor": "Microsoft", "service": "Clarity"},
                "documented_entity": {"vendor": "Microsoft", "service": "Azure OpenAI"}
            },
            {
                "type": "unresolved_document_reference",
                "status": "unresolved_document_reference",
                "documented_entity": {"vendor": "Unresolved Reference", "service": "Subprocessors", "purpose": "Vendor Processing"}
            }
        ]
        self.step7_nodes = [
            {
                "node_type": "service",
                "node_id": "NODE-svc-1",
                "vendor": "Microsoft",
                "service": "Clarity",
                "category": "Behavioural Analytics",
                "purpose": "Behavioural Analytics",
                "source": "Step 3 Intelligence",
                "evidence_refs": ["STEP3-CLARITY"]
            },
            {
                "node_type": "host",
                "node_id": "NODE-host-1",
                "name": "c.clarity.ms"
            }
        ]
        self.step7_edges = []
        self.step3_hosts = [
            {"domain": "c.clarity.ms", "vendor": "Microsoft"}
        ]

        self.resolver = EvidenceResolver(self.step2_consent, self.step6_graph, self.step6_disc, self.step7_nodes, self.step7_edges, self.step3_hosts)

    def test_schema_validity(self):
        builder = ActivityBuilder(self.resolver)
        act = builder.build_activity("Test Category", [self.step7_nodes[0]])
        self.assertIsInstance(act, ProcessingActivity)
        self.assertEqual(act.activity_name, "Test Category")

    def test_evidence_traceability(self):
        builder = ActivityBuilder(self.resolver)
        act = builder.build_activity("Behavioural Analytics", [self.step7_nodes[0]])
        self.assertIn("STEP3-CLARITY", act.evidence_refs)
        self.assertIn("STEP1-BROWSER", act.source.evidence_refs)

    def test_ambiguity_preservation(self):
        groups = group_activities(self.step7_nodes, self.step6_graph)
        self.assertIn("Behavioural Analytics", groups)
        self.assertIn("AI", groups)

        builder = ActivityBuilder(self.resolver)
        act1 = builder.build_activity("Behavioural Analytics", groups["Behavioural Analytics"])
        act2 = builder.build_activity("AI", groups["AI"])

        v1 = next((v for v in act1.vendors if v.service == "Clarity"), None)
        self.assertIsNotNone(v1)
        self.assertEqual(v1.reconciliation_status, "ambiguous_processing_entity")

        v2 = next((v for v in act2.vendors if v.service == "Azure OpenAI"), None)
        self.assertIsNotNone(v2)
        self.assertEqual(v2.reconciliation_status, "ambiguous_processing_entity")

    def test_unresolved_subprocessor(self):
        doc_node = {"vendor": "Unresolved Reference", "service": "Subprocessors", "purpose": "Vendor Processing", "category": "Vendor Processing", "source": "Step 5 Policy", "evidence_refs": ["REF1"]}
        builder = ActivityBuilder(self.resolver)
        act = builder.build_activity("Vendor Processing", [doc_node])

        v = act.vendors[0]
        self.assertEqual(v.vendor, "Unresolved Reference")
        self.assertEqual(v.reconciliation_status, "unresolved_document_reference")

    def test_consent_provenance(self):
        builder = ActivityBuilder(self.resolver)
        act = builder.build_activity("Behavioural Analytics", [self.step7_nodes[0]])

        c = act.consent_observation.value.get("c.clarity.ms")
        self.assertTrue(c["reject_all"])
        self.assertEqual(c["classification"], "present_across_states")

    def test_backend_unknowns(self):
        builder = ActivityBuilder(self.resolver)
        act = builder.build_activity("Behavioural Analytics", [self.step7_nodes[0]])
        self.assertEqual(act.storage_location, "not_available")
        self.assertEqual(act.automated_processing, "not_available")
        self.assertEqual(act.derived_data, "not_available")
        self.assertEqual(act.cross_border_observation.value, "not_available")

    def test_review_state(self):
        builder = ActivityBuilder(self.resolver)
        act = builder.build_activity("Behavioural Analytics", [self.step7_nodes[0]])
        self.assertEqual(act.status, "draft")
        self.assertTrue(act.requires_review)

    def test_determinism(self):
        builder = ActivityBuilder(self.resolver)
        act1 = builder.build_activity("Behavioural Analytics", [self.step7_nodes[0]])
        act2 = builder.build_activity("Behavioural Analytics", [self.step7_nodes[0]])
        self.assertEqual(act1.activity_id, act2.activity_id)

    def test_missing_incomplete_evidence(self):
        builder = ActivityBuilder(self.resolver)
        # Empty inputs should not crash or hallucinate
        act = builder.build_activity("Unknown", [{"vendor": None, "service": None}])
        self.assertEqual(act.vendors[0].vendor, "unknown")

if __name__ == '__main__':
    unittest.main()
