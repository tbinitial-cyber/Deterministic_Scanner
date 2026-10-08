import hashlib
from .schemas import ExistingControl, ResidualRisk
from .risk_rules import calculate_level

def generate_id(*args) -> str:
    return hashlib.md5("-".join([str(a) for a in args]).encode()).hexdigest()[:8]

class DPIAControlAssessor:
    def extract_controls(self, pa: dict, legal: list) -> list:
        controls = []
        pa_id = pa.get('activity_id')
        
        consent_legal = next((l for l in legal if l['rule_id'] == 'DPDPA_S6_CONSENT'), None)
        if consent_legal:
            if consent_legal['readiness_assessment'] == 'aligned':
                controls.append(ExistingControl(
                    control_id=f"CTRL-CON-{generate_id(pa_id)}",
                    processing_activity_id=pa_id,
                    control_type="consent management",
                    description="Consent gating actively blocks pre-consent telemetry.",
                    status="present",
                    effectiveness="effective",
                    evidence_refs=consent_legal['technical_evidence_refs']
                ))
            elif consent_legal['readiness_assessment'] == 'gap':
                controls.append(ExistingControl(
                    control_id=f"CTRL-CON-{generate_id(pa_id)}",
                    processing_activity_id=pa_id,
                    control_type="consent management",
                    description="Consent gating bypassed or ignored.",
                    status="present",
                    effectiveness="ineffective",
                    evidence_refs=consent_legal['technical_evidence_refs']
                ))
                
        notice_legal = next((l for l in legal if l['rule_id'] == 'DPDPA_S5_NOTICE'), None)
        if notice_legal:
            if notice_legal['readiness_assessment'] == 'aligned':
                controls.append(ExistingControl(
                    control_id=f"CTRL-NOT-{generate_id(pa_id)}",
                    processing_activity_id=pa_id,
                    control_type="privacy notice",
                    description="Processing explicitly documented.",
                    status="present",
                    effectiveness="effective",
                    evidence_refs=notice_legal['document_evidence_refs']
                ))
                
        # Security/Retention
        s8_legal = next((l for l in legal if l['rule_id'] == 'DPDPA_S8_GENERAL'), None)
        if s8_legal and s8_legal['readiness_assessment'] == 'insufficient_evidence':
            controls.append(ExistingControl(
                control_id=f"CTRL-SEC-{generate_id(pa_id)}",
                processing_activity_id=pa_id,
                control_type="security controls",
                description="Technical security measures unknown.",
                status="unknown",
                effectiveness="unknown",
                evidence_refs=[]
            ))
            
        return controls
        
    def calculate_residual(self, scenario, controls: list) -> ResidualRisk:
        r_like = scenario.likelihood
        r_impact = scenario.impact
        reasons = []
        
        # Determine effectiveness
        for ctrl in controls:
            if ctrl.effectiveness == 'effective':
                if ctrl.control_type == 'consent management' and scenario.risk_type == 'unexpected_tracking_or_collection':
                    r_like = max(1, r_like - 2)
                    reasons.append("Consent management present and effective.")
                if ctrl.control_type == 'privacy notice' and scenario.risk_type == 'transparency_mismatch':
                    r_like = max(1, r_like - 2)
                    reasons.append("Privacy notice explicitly covers processing.")
            
        score = r_like * r_impact
        return ResidualRisk(
            risk_id=scenario.risk_id,
            residual_likelihood=r_like,
            residual_impact=r_impact,
            residual_risk_score=score,
            residual_risk_level=calculate_level(score),
            reduction_reason=reasons or ["No effective controls observed to reduce risk."]
        )
