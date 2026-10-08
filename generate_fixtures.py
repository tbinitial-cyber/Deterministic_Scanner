import json
import os
import hashlib

def save(path, data):
    with open(path, 'w') as f: json.dump(data, f)

save("fixtures/synthetic/documents/document_manifest.json", {"documents": ["privacy_policy"]})
save("fixtures/synthetic/ropa/processing_activities.json", [{"id": "pa1", "description": "synthetic"}])
save("fixtures/synthetic/legal/control_assessments.json", [{"legal_relevance": "high", "current_enforceability": "in_force", "readiness_assessment": "aligned", "current_legal_violation": False}])
save("fixtures/synthetic/dpia/dpi_assessments.json", [{"residual_risks": [], "existing_controls": [], "statutory_dpia_status": "required"}])

def h(p):
    with open(p, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()

save("fixtures/synthetic/final/findings.json", [])
save("fixtures/synthetic/final/audit_manifest.json", {
    "output_hashes": {
        "findings.json": h("fixtures/synthetic/final/findings.json")
    }
})
