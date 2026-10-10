import unittest
import json
import os
import shutil
from step7.graph_builder import GraphBuilder
from step7.schemas import LineageNode, LineageEdge

class TestStep7(unittest.TestCase):
    def test_cookie_states_and_deduplication(self):
        cookies = [
            {"name": "_ga", "domain": ".example.com", "observed_in_scenarios": {"pre_consent_observed": True, "accept_all_observed": True, "reject_all_attempted_observed": True}}
        ]
        hosts = [
            {"domain": "api.example.com", "vendor": "Example", "category": "Analytics", "is_first_party": False}
        ]
        vendors = []
        behaviour = [
            {"target": "api.example.com", "pre_consent": True, "accept_all": True, "reject_all": True}
        ]

        builder = GraphBuilder(cookies, hosts, vendors, behaviour)
        graph = builder.build()

        # Check node types
        cookie_nodes = [n for n in graph.nodes if n.node_type == "cookie"]
        self.assertEqual(len(cookie_nodes), 1)
        self.assertEqual(cookie_nodes[0].name, "_ga")

        # Check edge states
        sends_to = [e for e in graph.edges if e.relationship == "sends_to"]
        self.assertEqual(len(sends_to), 1)
        self.assertTrue(sends_to[0].observed_in_scenarios["reject_all_attempted_observed"])
        self.assertNotIn("reject_all", sends_to[0].observed_in_scenarios)

        # Check cookie edges
        stored_in = [e for e in graph.edges if e.relationship == "stored_in"]
        self.assertEqual(len(stored_in), 1)
        self.assertTrue(stored_in[0].observed_in_scenarios["pre_consent_observed"])

        # Check no backend hallucination
        allowed_relationships = {"sends_to", "resolves_to", "classified_as", "scoped_to", "stored_in"}
        for e in graph.edges:
            self.assertIn(e.relationship, allowed_relationships)

if __name__ == '__main__':
    unittest.main()
