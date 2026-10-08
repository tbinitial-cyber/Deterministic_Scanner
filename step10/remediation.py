import hashlib
from .schemas import RemediationCandidate

def generate_id(*args) -> str:
    return hashlib.md5("-".join([str(a) for a in args]).encode()).hexdigest()[:8]

def generate_remediations(scenario) -> list:
    remediations = []
    pid = scenario.processing_activity_id
    rid = scenario.risk_id
    
    if scenario.risk_type == "transparency_mismatch":
        remediations.append(RemediationCandidate(
            remediation_id=f"REM-TNS-{generate_id(pid, rid)}",
            risk_id=rid,
            processing_activity_id=pid,
            remediation_type="Notice Update",
            description="review privacy notice against observed processing",
            priority="high" if scenario.inherent_risk_level in ['high', 'critical'] else "medium"
        ))
        
    elif scenario.risk_type == "unexpected_tracking_or_collection":
        remediations.append(RemediationCandidate(
            remediation_id=f"REM-TRK-{generate_id(pid, rid)}",
            risk_id=rid,
            processing_activity_id=pid,
            remediation_type="Consent Engineering",
            description="investigate consent-gate enforcement",
            priority="high"
        ))
        
    elif scenario.risk_type == "third_party_governance_risk":
        remediations.append(RemediationCandidate(
            remediation_id=f"REM-3RD-{generate_id(pid, rid)}",
            risk_id=rid,
            processing_activity_id=pid,
            remediation_type="Vendor Governance",
            description="obtain/review processor documentation",
            priority="medium"
        ))
        
    elif scenario.risk_type == "retention_governance_uncertainty":
        remediations.append(RemediationCandidate(
            remediation_id=f"REM-RET-{generate_id(pid, rid)}",
            risk_id=rid,
            processing_activity_id=pid,
            remediation_type="Data Lifecycle",
            description="obtain documented retention schedule and backend evidence",
            priority="medium"
        ))
        
    elif scenario.risk_type == "security_assurance_gap":
        remediations.append(RemediationCandidate(
            remediation_id=f"REM-SEC-{generate_id(pid, rid)}",
            risk_id=rid,
            processing_activity_id=pid,
            remediation_type="Security Audit",
            description="perform cloud/database security assessment",
            priority="medium"
        ))
        
    return remediations
