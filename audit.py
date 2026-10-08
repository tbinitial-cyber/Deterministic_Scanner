import sys
import os
import json
import argparse
import subprocess
from datetime import datetime, timezone

def compute_sha256(filepath):
    import hashlib
    sha256_hash = hashlib.sha256()
    if not os.path.exists(filepath):
        return None
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_json(path):
    if not os.path.exists(path): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

STEPS = {
    1: {"name": "Raw Telemetry Capture", "cmd": "python scan.py {url} --window {window}", "manifest": "output/scan_manifest.json", "reserved": False},
    2: {"name": "Consent Behaviour", "cmd": "python step2/consent_runner.py", "manifest": "output/consent_audit/consent_manifest.json", "reserved": False},
    3: {"name": "Data Flow Intelligence", "cmd": "python step3/intelligence_runner.py", "manifest": "output/data_flow/intelligence_manifest.json", "reserved": False},
    4: {"name": "Cloud/DB Discovery", "cmd": "", "manifest": "", "reserved": True, "reason": "Controlled cloud/database environment not yet available"},
    5: {"name": "Document Parsing", "cmd": "python step5/document_runner.py", "manifest": "output/documents/document_manifest.json", "reserved": False},
    6: {"name": "Reconciliation", "cmd": "python step6/reconciliation_runner.py", "manifest": "output/reconciliation/reconciliation_manifest.json", "reserved": False},
    7: {"name": "Lineage", "cmd": "python step7/lineage_runner.py", "manifest": "output/lineage/lineage_manifest.json", "reserved": False},
    8: {"name": "Governance Register", "cmd": "python step8/ropa_runner.py", "manifest": "output/ropa/ropa_manifest.json", "reserved": False},
    9: {"name": "Legal Obligation Mapping", "cmd": "python step9/legal_runner.py", "manifest": "output/legal/legal_manifest.json", "reserved": False},
    10: {"name": "DPIA Engine", "cmd": "python step10/dpia_runner.py", "manifest": "output/dpia/dpia_manifest.json", "reserved": False},
}

DEPENDENCIES = {
    2: [1],
    3: [1],
    5: [1],
    6: [3, 5],
    7: [1, 2, 3, 5, 6],
    8: [2, 3, 5, 6, 7],
    9: [8],
    10: [8, 9]
}

class AuditOrchestrator:
    def __init__(self, url, window, output_dir, from_step):
        self.url = url
        self.window = window
        self.output_dir = output_dir
        self.from_step = from_step
        
        self.manifest_data = {
            "audit_id": f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "version": "v1.0.0-core",
            "target_url": url,
            "execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "scanner_version": "v1.0.0-core",
            "pipeline_version": "v1.0.0-core",
            "step_statuses": {},
            "step_manifests": {},
            "input_hashes": {},
            "output_hashes": {},
            "reserved_steps": [],
            "failures": []
        }

    def validate_manifest(self, step_id, manifest_path):
        if not os.path.exists(manifest_path):
            return False, f"Manifest missing: {manifest_path}"
        
        man = load_json(manifest_path)
        out_hashes = man.get('output_hashes', man.get('files', {}))
        base_dir = os.path.dirname(manifest_path)
        if step_id == 1:
            base_dir = "output"
            
        for fname, exp_hash in out_hashes.items():
            fpath = os.path.join(base_dir, fname)
            actual_hash = compute_sha256(fpath)
            if actual_hash != exp_hash:
                return False, f"Hash mismatch for {fpath}: expected {exp_hash}, got {actual_hash}"
                
        return True, man

    def run(self):
        print(f"=== Starting Deterministic Audit Orchestrator ===")
        print(f"Target: {self.url} | From Step: {self.from_step}")
        
        for step_id in range(1, 11):
            step = STEPS[step_id]
            print(f"\n--- Step {step_id}: {step['name']} ---")
            
            if step['reserved']:
                print(f"Status: RESERVED - {step['reason']}")
                self.manifest_data["step_statuses"][f"step_{step_id}"] = {"status": "reserved", "reason": step['reason']}
                self.manifest_data["reserved_steps"].append(step_id)
                continue
                
            if step_id < self.from_step:
                print("Skipping execution (prior to from_step). Validating existing manifest...")
                valid, result = self.validate_manifest(step_id, step['manifest'])
                if not valid:
                    print(f"Validation FAILED: {result}")
                    self.record_failure(step_id, result)
                    return
                print("Validation SUCCESS. Existing outputs verified.")
                self.record_success(step_id, step['manifest'], result)
                continue
                
            # Check upstream dependencies
            deps = DEPENDENCIES.get(step_id, [])
            for dep_id in deps:
                dep_status = self.manifest_data["step_statuses"].get(f"step_{dep_id}", {}).get("status")
                if dep_status != "completed":
                    err = f"Dependency Step {dep_id} is not completed. Status: {dep_status}"
                    print(f"FAILED: {err}")
                    self.record_failure(step_id, err)
                    return
                    
            # Execute
            cmd = step['cmd'].replace("{url}", self.url).replace("{window}", str(self.window))
            print(f"Executing: {cmd}")
            try:
                res = subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                err = f"Execution failed with return code {e.returncode}"
                print(f"FAILED: {err}")
                self.record_failure(step_id, err)
                return
                
            # Post-execution validation
            valid, result = self.validate_manifest(step_id, step['manifest'])
            if not valid:
                print(f"Validation FAILED after execution: {result}")
                self.record_failure(step_id, result)
                return
                
            print("Execution and Validation SUCCESS.")
            self.record_success(step_id, step['manifest'], result)

        self.generate_final_package()

    def record_failure(self, step_id, error_msg):
        self.manifest_data["step_statuses"][f"step_{step_id}"] = {"status": "failed", "error": error_msg}
        self.manifest_data["failures"].append({"step": step_id, "error": error_msg})
        print(f"\n!!! Pipeline stopped due to failure at Step {step_id} !!!")

    def record_success(self, step_id, manifest_path, manifest_data):
        m_hash = compute_sha256(manifest_path)
        self.manifest_data["step_statuses"][f"step_{step_id}"] = {
            "status": "completed",
            "manifest": manifest_path,
            "manifest_hash": m_hash
        }
        self.manifest_data["step_manifests"][f"step_{step_id}"] = manifest_data
        
    def generate_final_package(self):
        print("\n=== Generating Final Audit Package ===")
        os.makedirs(os.path.join(self.output_dir, "final"), exist_ok=True)
        
        # 1. Findings (Aggregated)
        findings = []
        evidence_index = {}
        
        # Step 6 Discrepancies
        discrepancies = load_json("output/reconciliation/discrepancies.json")
        for d in discrepancies:
            obs_ent = d.get('observed_entity') or {}
            doc_ent = d.get('documented_entity') or {}
            entity_name = obs_ent.get('service') or doc_ent.get('service') or obs_ent.get('vendor') or doc_ent.get('vendor') or 'unk'
            fid = f"FIND-REC-{entity_name.replace(' ', '')}"
            findings.append({
                "finding_id": fid,
                "source_step": 6,
                "type": "reconciliation_discrepancy",
                "severity/status": d.get('status'),
                "evidence_refs": d.get('evidence_refs', []),
                "processing_activity_id": None,
                "requires_review": True
            })
            for ref in d.get('evidence_refs', []):
                evidence_index.setdefault(ref, []).append(fid)
                
        # Step 9 Legal Gaps
        legal_gaps = load_json("output/legal/gaps.json")
        for g in legal_gaps:
            fid = f"FIND-LAW-{g.get('assessment_id')}"
            findings.append({
                "finding_id": fid,
                "source_step": 9,
                "type": "legal_control_gap",
                "severity/status": g.get('readiness_assessment', 'gap'),
                "evidence_refs": g.get('technical_evidence_refs', []) + g.get('document_evidence_refs', []),
                "processing_activity_id": g.get('processing_activity_id'),
                "requires_review": g.get('requires_human_review', False)
            })
            for ref in g.get('technical_evidence_refs', []) + g.get('document_evidence_refs', []):
                evidence_index.setdefault(ref, []).append(fid)
                
        # Step 10 Risks
        risks = load_json("output/dpia/risk_register.json")
        for r in risks:
            fid = f"FIND-RSK-{r.get('risk_id')}"
            findings.append({
                "finding_id": fid,
                "source_step": 10,
                "type": "privacy_risk",
                "severity/status": r.get('inherent_risk_level', 'unknown'),
                "evidence_refs": r.get('technical_evidence_refs', []) + r.get('legal_refs', []),
                "processing_activity_id": r.get('processing_activity_id'),
                "requires_review": r.get('inherent_risk_level') in ['high', 'critical']
            })
            for ref in r.get('technical_evidence_refs', []) + r.get('legal_refs', []):
                evidence_index.setdefault(ref, []).append(fid)

        save_json(findings, os.path.join(self.output_dir, "final/findings.json"))
        
        # 2. Remediation
        remediations = load_json("output/dpia/remediation_plan.json")
        rem_out = []
        for rm in remediations:
            r_id = rm.get('risk_id')
            # Look up risk to inherit its evidence refs
            parent_risk = next((r for r in risks if r.get('risk_id') == r_id), {})
            inherited_refs = parent_risk.get('technical_evidence_refs', []) + parent_risk.get('legal_refs', []) + [r_id]
            
            rem_out.append({
                "remediation_id": rm.get('remediation_id'),
                "risk_id": r_id,
                "processing_activity_id": rm.get('processing_activity_id'),
                "priority": rm.get('priority'),
                "description": rm.get('description'),
                "evidence_refs": list(set(inherited_refs))
            })
            evidence_index.setdefault(r_id, []).append(rm.get('remediation_id'))
        save_json(rem_out, os.path.join(self.output_dir, "final/remediation.json"))
        
        # 3. Evidence Index
        save_json(evidence_index, os.path.join(self.output_dir, "final/evidence_index.json"))
        
        # 4. Summary
        hosts = load_json("output/data_flow/hosts.json")
        ropa = load_json("output/ropa/processing_activities.json")
        
        summary = {
            "target": self.url,
            "scan_timestamp": self.manifest_data['execution_timestamp'],
            "observed_frontend_surface": {
                "total_hosts": len(hosts),
                "first_party_hosts": len([h for h in hosts if h.get('is_first_party')]),
                "third_party_hosts": len([h for h in hosts if not h.get('is_first_party')]),
                "vendors": len(load_json("output/data_flow/vendors.json")),
                "trackers": len(load_json("output/data_flow/trackers.json"))
            },
            "consent_findings": len([f for f in findings if f['source_step'] == 6 and 'consent' in f['finding_id'].lower()]),
            "reconciliation_discrepancies": len(discrepancies),
            "processing_activities": len(ropa),
            "legal_assessments": len(legal_gaps) + len([a for a in load_json("output/legal/control_assessments.json") if a.get('readiness_assessment') != 'gap']),
            "readiness_gaps": len(legal_gaps),
            "risk_count": len(risks),
            "high_risk_count": len([r for r in risks if r.get('inherent_risk_level') in ['high', 'critical']]),
            "remediation_count": len(remediations),
            "human_review_count": len(load_json("output/dpia/human_review_queue.json")),
            "reserved_capabilities": self.manifest_data["reserved_steps"]
        }
        save_json(summary, os.path.join(self.output_dir, "final/audit_summary.json"))
        
        # 5. Manifest
        self.manifest_data["output_hashes"] = {
            "findings.json": compute_sha256(os.path.join(self.output_dir, "final/findings.json")),
            "remediation.json": compute_sha256(os.path.join(self.output_dir, "final/remediation.json")),
            "evidence_index.json": compute_sha256(os.path.join(self.output_dir, "final/evidence_index.json")),
            "audit_summary.json": compute_sha256(os.path.join(self.output_dir, "final/audit_summary.json"))
        }
        save_json(self.manifest_data, os.path.join(self.output_dir, "final/audit_manifest.json"))
        print(f"\n[OK] Audit complete. Package generated in {self.output_dir}/final/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Privacy Audit Orchestrator")
    parser.add_argument("url", nargs="?", default="https://miro.com", help="Target URL to audit")
    parser.add_argument("--window", type=int, default=10000, help="Observation window in ms")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--from-step", type=int, default=1, help="Start execution from this step (validates upstream)")
    args = parser.parse_args()
    
    orchestrator = AuditOrchestrator(args.url, args.window, args.output, args.from_step)
    orchestrator.run()
