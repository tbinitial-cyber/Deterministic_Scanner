import hashlib
from .schemas import RiskScenario
from .risk_rules import calculate_level

def generate_id(*args) -> str:
    return hashlib.md5("-".join([str(a) for a in args]).encode()).hexdigest()[:8]

class RiskEngine:
    def generate_scenarios(self, pa: dict, factors: list, legal: list) -> list:
        scenarios = []
        pa_id = pa.get('activity_id')
        
        # 1. Unexpected Tracking
        if "tracking / behavioural analytics" in factors:
            consent_legal = next((l for l in legal if l['rule_id'] == 'DPDPA_S6_CONSENT'), None)
            if consent_legal and consent_legal['readiness_assessment'] == 'gap':
                score = 4 * 4
                scenarios.append(RiskScenario(
                    risk_id=f"RSK-TRK-{generate_id(pa_id)}",
                    processing_activity_id=pa_id,
                    risk_type="unexpected_tracking_or_collection",
                    description="Behavioural tracking observed without functioning consent gating.",
                    likelihood=4,
                    impact=4,
                    inherent_risk_score=score,
                    inherent_risk_level=calculate_level(score),
                    scoring_reason=["behavioural tracking observed", "consent discrepancy identified"],
                    technical_evidence_refs=consent_legal['technical_evidence_refs'],
                    reconciliation_refs=[],
                    legal_refs=[consent_legal['assessment_id']]
                ))

        # 2. Transparency Mismatch
        if "consent/documentation mismatch" in factors:
            notice_legal = next((l for l in legal if l['rule_id'] == 'DPDPA_S5_NOTICE'), None)
            if notice_legal and notice_legal['readiness_assessment'] in ['gap', 'requires_human_review']:
                score = 4 * 3
                scenarios.append(RiskScenario(
                    risk_id=f"RSK-TNS-{generate_id(pa_id)}",
                    processing_activity_id=pa_id,
                    risk_type="transparency_mismatch",
                    description="Processing activity not explicitly documented in notice.",
                    likelihood=4,
                    impact=3,
                    inherent_risk_score=score,
                    inherent_risk_level=calculate_level(score),
                    scoring_reason=["observed processing", "documentation discrepancy"],
                    technical_evidence_refs=[],
                    reconciliation_refs=notice_legal['reconciliation_refs'],
                    legal_refs=[notice_legal['assessment_id']]
                ))
                
        # 3. Third-party Governance
        if "multiple third parties" in factors and "security-control uncertainty" in factors:
            s8_legal = next((l for l in legal if l['rule_id'] == 'DPDPA_S8_GENERAL'), None)
            score = 3 * 3
            scenarios.append(RiskScenario(
                risk_id=f"RSK-3RD-{generate_id(pa_id)}",
                processing_activity_id=pa_id,
                risk_type="third_party_governance_risk",
                description="Third-party processor engaged with unclear contractual/security evidence.",
                likelihood=3,
                impact=3,
                inherent_risk_score=score,
                inherent_risk_level=calculate_level(score),
                scoring_reason=["third-party processing observed", "unclear documentation / contractual evidence"],
                technical_evidence_refs=[],
                reconciliation_refs=[],
                legal_refs=[s8_legal['assessment_id']] if s8_legal else []
            ))
            
        # 4. Retention Governance
        if "retention uncertainty" in factors:
            r8_legal = next((l for l in legal if l['rule_id'] == 'DPDPR_R8_RETENTION'), None)
            score = 3 * 2
            scenarios.append(RiskScenario(
                risk_id=f"RSK-RET-{generate_id(pa_id)}",
                processing_activity_id=pa_id,
                risk_type="retention_governance_uncertainty",
                description="Retention schedule and backend erasure evidence unavailable.",
                likelihood=3,
                impact=2,
                inherent_risk_score=score,
                inherent_risk_level=calculate_level(score),
                scoring_reason=["retention evidence unavailable"],
                technical_evidence_refs=[],
                reconciliation_refs=[],
                legal_refs=[r8_legal['assessment_id']] if r8_legal else []
            ))

        # 5. Security Assurance Gap
        if "security-control uncertainty" in factors:
            s8_legal = next((l for l in legal if l['rule_id'] == 'DPDPA_S8_GENERAL'), None)
            score = 3 * 4
            scenarios.append(RiskScenario(
                risk_id=f"RSK-SEC-{generate_id(pa_id)}",
                processing_activity_id=pa_id,
                risk_type="security_assurance_gap",
                description="Backend/security evidence unavailable for observed processing.",
                likelihood=3,
                impact=4,
                inherent_risk_score=score,
                inherent_risk_level=calculate_level(score),
                scoring_reason=["backend/security evidence unavailable"],
                technical_evidence_refs=[],
                reconciliation_refs=[],
                legal_refs=[s8_legal['assessment_id']] if s8_legal else []
            ))

        return scenarios
