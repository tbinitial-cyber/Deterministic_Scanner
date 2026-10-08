import sys
import os
import argparse
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_json, compute_sha256
from step6.schemas import ReconciliationManifest
from step6.graph_builder import GraphBuilder
from step6.entity_matcher import match_entities
from step6.discrepancy_rules import evaluate_results

def run_reconciliation():
    print("=== Starting Step 6 Hybrid Reality vs Documentation Reconciliation ===")
    
    step3_path = "output/data_flow"
    step5_path = "output/documents"
    out_dir = "output/reconciliation"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Build Graphs
    print("Building Processing Entities...")
    builder = GraphBuilder(step3_path, step5_path)
    observed = builder.build_observed()
    documented = builder.build_documented()
    
    # 2. Match
    print("Executing Deterministic Matcher...")
    results = match_entities(observed, documented)
    matches = [r for r in results if r['match_type'] == 'matched']
    
    # 3. Discrepancy Rules
    print("Evaluating Discrepancies...")
    dpa_path = os.path.join(step5_path, "dpa_facts.json")
    discrepancies = evaluate_results(results, dpa_path)
    
    # 4. Save Outputs
    save_json([o.model_dump() for o in observed], os.path.join(out_dir, "observed_entities.json"))
    save_json([d.model_dump() for d in documented], os.path.join(out_dir, "documented_entities.json"))
    
    # Serialize results graph
    serializable_results = []
    for r in results:
        sr = r.copy()
        if sr['observed']: sr['observed'] = sr['observed'].model_dump()
        if sr['documented']: sr['documented'] = sr['documented'].model_dump()
        serializable_results.append(sr)
        
    save_json(serializable_results, os.path.join(out_dir, "evidence_graph.json"))
    
    serializable_matches = [m for m in serializable_results if m['match_type'] == 'matched']
    save_json(serializable_matches, os.path.join(out_dir, "matched_entities.json"))
    save_json([d.model_dump() for d in discrepancies], os.path.join(out_dir, "discrepancies.json"))
    
    # Cryptographic Provenance
    input_hashes = {}
    for f in ['hosts.json', 'vendors.json', 'trackers.json', 'cookies_enriched.json', 'data_flow_graph.json']:
        p = os.path.join(step3_path, f)
        if os.path.exists(p): input_hashes[f"step3/{f}"] = compute_sha256(p)
        
    for f in ['policy_facts.json', 'dpa_facts.json', 'subprocessors.json', 'document_manifest.json']:
        p = os.path.join(step5_path, f)
        if os.path.exists(p): input_hashes[f"step5/{f}"] = compute_sha256(p)
        
    output_hashes = {
        "evidence_graph.json": compute_sha256(os.path.join(out_dir, "evidence_graph.json")),
        "discrepancies.json": compute_sha256(os.path.join(out_dir, "discrepancies.json"))
    }
    
    manifest = ReconciliationManifest(
        target_url="https://miro.com",
        timestamp=datetime.now(timezone.utc).isoformat(),
        input_hashes=input_hashes,
        output_hashes=output_hashes,
        total_observed=len(observed),
        total_documented=len(documented),
        total_matched=len(matches),
        total_discrepancies=len(discrepancies)
    )
    save_json(manifest.model_dump(), os.path.join(out_dir, "reconciliation_manifest.json"))
    
    print("\nStep 6 Complete. Discrepancies generated:")
    for d in discrepancies:
        print(f"- {d.type}: Obs:{d.observed_entity.service if d.observed_entity else 'None'} vs Doc:{d.documented_entity.service if d.documented_entity else 'None'} ({d.match_reason})")

if __name__ == "__main__":
    run_reconciliation()
