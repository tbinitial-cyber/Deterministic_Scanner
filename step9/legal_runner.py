import sys
import os
import json
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_json, compute_sha256
from step9.schemas import LegalManifest
from step9.legal_loader import load_knowledge_base
from step9.commencement import inject_commencement
from step9.applicability_engine import get_applicable_obligations
from step9.control_assessor import ControlAssessor

def load_json(path: str):
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_legal_engine():
    print("=== Starting Step 9 DPDPA Legal Obligation & Control Mapping Engine ===")
    
    in_paths = {
        "step8_ropa": "output/ropa/processing_activities.json",
        "legal_act": "legal/dpdpa_obligations.yaml",
        "legal_rules": "legal/dpdp_rules.yaml"
    }
    
    ropa = load_json(in_paths["step8_ropa"])
    
    # 1. Load Knowledge Base
    print("Loading legal knowledge base...")
    obligations = load_knowledge_base("legal")
    
    # 2. Inject Commencement
    obligations_dicts = [o.model_dump() for o in obligations]
    obligations_dicts = inject_commencement(obligations_dicts)
    
    # Convert back to objects for strict processing
    from step9.schemas import LegalObligation
    obligations = [LegalObligation(**o) for o in obligations_dicts]
    
    assessor = ControlAssessor()
    all_applicable = []
    all_assessments = []
    
    print("Mapping obligations and assessing controls...")
    for pa in ropa:
        # 3. Applicability
        applicable = get_applicable_obligations(pa, obligations)
        all_applicable.extend([{
            "processing_activity_id": pa.get('activity_id'),
            "rule_id": a.rule_id,
            "provision": a.provision
        } for a in applicable])
        
        # 4. Assess
        for obs in applicable:
            assessment = assessor.evaluate(pa, obs)
            all_assessments.append(assessment)
            
    # Outputs
    out_dir = "output/legal"
    os.makedirs(out_dir, exist_ok=True)
    
    save_json(all_applicable, os.path.join(out_dir, "applicable_obligations.json"))
    save_json([a.model_dump() for a in all_assessments], os.path.join(out_dir, "control_assessments.json"))
    
    gaps = [a.model_dump() for a in all_assessments if a.readiness_assessment == 'gap']
    save_json(gaps, os.path.join(out_dir, "gaps.json"))
    
    # Manifest
    input_hashes = {}
    for name, path in in_paths.items():
        if os.path.exists(path):
            input_hashes[name] = compute_sha256(path)
            
    output_hashes = {
        "applicable_obligations.json": compute_sha256(os.path.join(out_dir, "applicable_obligations.json")),
        "control_assessments.json": compute_sha256(os.path.join(out_dir, "control_assessments.json")),
        "gaps.json": compute_sha256(os.path.join(out_dir, "gaps.json"))
    }
    
    manifest = LegalManifest(
        target_url="https://miro.com",
        timestamp=datetime.now(timezone.utc).isoformat(),
        input_hashes=input_hashes,
        output_hashes=output_hashes,
        total_assessments=len(all_assessments)
    )
    save_json(manifest.model_dump(), os.path.join(out_dir, "legal_manifest.json"))
    
    print(f"Step 9 Complete. Generated {len(all_assessments)} Control Assessments across {len(ropa)} Processing Activities.")
    print(f"Detected {len(gaps)} deterministic control gaps.")

if __name__ == "__main__":
    run_legal_engine()
