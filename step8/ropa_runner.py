import sys
import os
import json
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_json, compute_sha256
from step8.schemas import RopaManifest
from step8.evidence_resolver import EvidenceResolver
from step8.activity_grouping import group_activities
from step8.activity_builder import ActivityBuilder

def load_json(path: str):
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_ropa():
    print("=== Starting Step 8 DPDPA Processing Governance Register ===")
    
    in_paths = {
        "step2_consent": "output/consent_audit/behaviour_findings.json",
        "step3_hosts": "output/data_flow/hosts.json",
        "step3_vendors": "output/data_flow/vendors.json",
        "step5_policy": "output/documents/policy_facts.json",
        "step6_graph": "output/reconciliation/evidence_graph.json",
        "step6_disc": "output/reconciliation/discrepancies.json",
        "step7_nodes": "output/lineage/nodes.json",
        "step7_edges": "output/lineage/edges.json"
    }
    
    step2_consent = load_json(in_paths["step2_consent"])
    step3_hosts = load_json(in_paths["step3_hosts"])
    step6_graph = load_json(in_paths["step6_graph"])
    step6_disc = load_json(in_paths["step6_disc"])
    step7_nodes = load_json(in_paths["step7_nodes"])
    step7_edges = load_json(in_paths["step7_edges"])
    
    resolver = EvidenceResolver(step2_consent, step6_graph, step6_disc, step7_nodes, step7_edges, step3_hosts)
    
    # Group entities into activities
    print("Clustering activities based on Category/Purpose...")
    groups = group_activities(step7_nodes, step6_graph)
    
    # Build Activities
    print("Building Processing Activities...")
    builder = ActivityBuilder(resolver)
    activities = []
    for cat, entities in groups.items():
        if cat == 'Other / Unknown': continue # Skip building a formal activity for unknowns
        activities.append(builder.build_activity(cat, entities))
        
    out_dir = "output/ropa"
    os.makedirs(out_dir, exist_ok=True)
    
    # Extract subsets for different registers
    third_party_register = []
    for a in activities:
        third_party_register.extend([v.model_dump() for v in a.vendors])
        
    consent_register = {}
    for a in activities:
        consent_register.update(a.consent_observation.value)
        
    save_json([a.model_dump() for a in activities], os.path.join(out_dir, "processing_activities.json"))
    save_json(third_party_register, os.path.join(out_dir, "third_party_register.json"))
    save_json(consent_register, os.path.join(out_dir, "consent_register.json"))
    
    # Manifest
    input_hashes = {}
    for name, path in in_paths.items():
        if os.path.exists(path):
            input_hashes[name] = compute_sha256(path)
            
    output_hashes = {
        "processing_activities.json": compute_sha256(os.path.join(out_dir, "processing_activities.json")),
        "third_party_register.json": compute_sha256(os.path.join(out_dir, "third_party_register.json")),
        "consent_register.json": compute_sha256(os.path.join(out_dir, "consent_register.json"))
    }
    
    manifest = RopaManifest(
        target_url="https://miro.com",
        timestamp=datetime.now(timezone.utc).isoformat(),
        input_hashes=input_hashes,
        output_hashes=output_hashes,
        total_activities=len(activities),
        total_vendors=len(third_party_register)
    )
    save_json(manifest.model_dump(), os.path.join(out_dir, "ropa_manifest.json"))
    
    print(f"Step 8 Complete. Generated {len(activities)} Processing Activities.")

if __name__ == "__main__":
    run_ropa()
