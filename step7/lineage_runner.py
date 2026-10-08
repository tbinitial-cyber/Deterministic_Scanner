import sys
import os
import json
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_json, compute_sha256
from step7.schemas import LineageManifest
from step7.graph_builder import GraphBuilder

def load_json(path: str):
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_lineage():
    print("=== Starting Step 7 Data Lineage Reconstruction ===")
    
    # Define inputs
    in_paths = {
        "step1/cookies.json": "output/cookies.json",
        "step2/behaviour_findings.json": "output/consent_audit/behaviour_findings.json",
        "step3/hosts.json": "output/data_flow/hosts.json",
        "step3/vendors.json": "output/data_flow/vendors.json",
        "step5/policy_facts.json": "output/documents/policy_facts.json",
        "step6/evidence_graph.json": "output/reconciliation/evidence_graph.json"
    }
    
    # Load data
    cookies = load_json(in_paths["step1/cookies.json"])
    behaviour = load_json(in_paths["step2/behaviour_findings.json"])
    hosts = load_json(in_paths["step3/hosts.json"])
    vendors = load_json(in_paths["step3/vendors.json"])
    
    # Build Graph
    builder = GraphBuilder(cookies, hosts, vendors, behaviour)
    graph = builder.build()
    
    # Save outputs
    out_dir = "output/lineage"
    os.makedirs(out_dir, exist_ok=True)
    
    save_json([n.model_dump() for n in graph.nodes], os.path.join(out_dir, "nodes.json"))
    save_json([e.model_dump() for e in graph.edges], os.path.join(out_dir, "edges.json"))
    save_json(graph.model_dump(), os.path.join(out_dir, "lineage_graph.json"))
    
    # Cryptographic Provenance
    input_hashes = {}
    for name, path in in_paths.items():
        if os.path.exists(path):
            input_hashes[name] = compute_sha256(path)
            
    output_hashes = {
        "nodes.json": compute_sha256(os.path.join(out_dir, "nodes.json")),
        "edges.json": compute_sha256(os.path.join(out_dir, "edges.json")),
        "lineage_graph.json": compute_sha256(os.path.join(out_dir, "lineage_graph.json"))
    }
    
    manifest = LineageManifest(
        target_url="https://miro.com",
        timestamp=datetime.now(timezone.utc).isoformat(),
        input_hashes=input_hashes,
        output_hashes=output_hashes,
        total_nodes=len(graph.nodes),
        total_edges=len(graph.edges)
    )
    save_json(manifest.model_dump(), os.path.join(out_dir, "lineage_manifest.json"))
    
    print("Step 7 Complete.")
    print(f"Total Nodes generated: {manifest.total_nodes}")
    print(f"Total Edges generated: {manifest.total_edges}")

if __name__ == "__main__":
    run_lineage()
