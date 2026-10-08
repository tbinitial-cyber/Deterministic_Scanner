import sys
import os
import json
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_json, compute_sha256
from step10.schemas import DPIAssessment, DPIAManifest
from step10.risk_rules import evaluate_risk_factors
from step10.risk_engine import RiskEngine
from step10.control_assessor import DPIAControlAssessor
from step10.remediation import generate_remediations

def load_json(path: str):
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_dpia_engine():
    print("=== Starting Step 10 DPIA & Privacy Risk Assessment Engine ===")
    
    in_paths = {
        "step8_ropa": "output/ropa/processing_activities.json",
        "step9_legal": "output/legal/control_assessments.json"
    }
    
    ropa = load_json(in_paths["step8_ropa"])
    legal_assessments = load_json(in_paths["step9_legal"])
    
    engine = RiskEngine()
    control_assessor = DPIAControlAssessor()
    
    dpi_assessments = []
    all_risks = []
    all_controls = []
    all_remediations = []
    human_queue = []
    
    print("Evaluating Processing Activities for privacy risk...")
    for pa in ropa:
        pa_id = pa.get('activity_id')
        pa_legal = [l for l in legal_assessments if l['processing_activity_id'] == pa_id]
        
        # 1. Factors
        factors = evaluate_risk_factors(pa, pa_legal)
        
        # 2. Risk Scenarios
        scenarios = engine.generate_scenarios(pa, factors, pa_legal)
        all_risks.extend(scenarios)
        
        # 3. Controls
        controls = control_assessor.extract_controls(pa, pa_legal)
        all_controls.extend(controls)
        
        # 4. Residual Risks
        residuals = [control_assessor.calculate_residual(scen, controls) for scen in scenarios]
        
        # 5. Remediations
        remediations = []
        for scen in scenarios:
            remediations.extend(generate_remediations(scen))
        all_remediations.extend(remediations)
        
        # Human Review check
        hr = False
        for scen in scenarios:
            if scen.inherent_risk_level in ['high', 'critical']:
                hr = True
        
        # Statutory Status (as specified, unknown for ordinary website without SDF evidence)
        stat_status = "unknown"
        
        dpia = DPIAssessment(
            assessment_id=f"DPIA-{pa_id}",
            processing_activity_id=pa_id,
            processing_description=pa.get('description', 'not_available'),
            purpose=pa.get('purpose', {}).get('value', 'unknown'),
            data_categories=pa.get('data_categories', {}).get('value', []),
            data_subjects=pa.get('data_subject_category', {}).get('value', 'unknown'),
            vendors=[v.get('vendor', 'unknown') for v in pa.get('vendors', [])],
            recipients=pa.get('recipients', []),
            transfers=pa.get('cross_border_observation', {}).get('value', 'unknown'),
            automated_processing=pa.get('automated_processing', 'not_available'),
            profiling="unknown",
            consent_characteristics=json.dumps(pa.get('consent_observation', {}).get('value', {})),
            risk_factors=factors,
            risk_scenarios=scenarios,
            existing_controls=controls,
            residual_risks=residuals,
            mitigations=remediations,
            statutory_dpia_status=stat_status,
            requires_human_review=hr,
            evidence_refs=[]
        )
        dpi_assessments.append(dpia)
        if hr: human_queue.append(dpia)

    # Outputs
    out_dir = "output/dpia"
    os.makedirs(out_dir, exist_ok=True)
    
    save_json([d.model_dump() for d in dpi_assessments], os.path.join(out_dir, "dpi_assessments.json"))
    save_json([r.model_dump() for r in all_risks], os.path.join(out_dir, "risk_register.json"))
    save_json([c.model_dump() for c in all_controls], os.path.join(out_dir, "control_assessments.json"))
    save_json([m.model_dump() for m in all_remediations], os.path.join(out_dir, "remediation_plan.json"))
    save_json([d.model_dump() for d in human_queue], os.path.join(out_dir, "human_review_queue.json"))
    
    # Manifest
    input_hashes = {}
    for name, path in in_paths.items():
        if os.path.exists(path):
            input_hashes[name] = compute_sha256(path)
            
    output_hashes = {
        "dpi_assessments.json": compute_sha256(os.path.join(out_dir, "dpi_assessments.json")),
        "risk_register.json": compute_sha256(os.path.join(out_dir, "risk_register.json")),
        "control_assessments.json": compute_sha256(os.path.join(out_dir, "control_assessments.json")),
        "remediation_plan.json": compute_sha256(os.path.join(out_dir, "remediation_plan.json"))
    }
    
    manifest = DPIAManifest(
        target_url="https://miro.com",
        timestamp=datetime.now(timezone.utc).isoformat(),
        input_hashes=input_hashes,
        output_hashes=output_hashes,
        total_assessments=len(dpi_assessments),
        total_risks=len(all_risks)
    )
    save_json(manifest.model_dump(), os.path.join(out_dir, "dpia_manifest.json"))
    
    print(f"Step 10 Complete. Evaluated {len(dpi_assessments)} activities.")
    print(f"Identified {len(all_risks)} deterministic risk scenarios.")

if __name__ == "__main__":
    run_dpia_engine()
