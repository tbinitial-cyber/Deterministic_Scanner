import hashlib
from .schemas import ControlAssessment

def generate_id(*args) -> str:
    return hashlib.md5("-".join([str(a) for a in args]).encode()).hexdigest()[:8]

class ControlAssessor:
    def evaluate(self, pa: dict, obs) -> ControlAssessment:
        test_name = obs.technical_test
        state = "requires_human_review"
        reason = "No automated test implemented"
        
        doc_refs = []
        tech_refs = []
        recon_refs = []
        
        # Pull global refs from PA
        recon_status = pa.get('documentation_status', 'unknown')
        
        if test_name == 'check_notice_documentation':
            if recon_status == 'matched':
                state = 'aligned'
                reason = "Notice documentation matches observed processing."
            elif recon_status in ['not_documented', 'observed_entity_not_documented']:
                state = 'gap'
                reason = "Observed processing lacks explicit notice documentation."
            elif recon_status in ['ambiguous', 'partial', 'ambiguous_processing_entity']:
                state = 'requires_human_review'
                reason = "Notice documentation is ambiguous or partially matched."
            else:
                state = 'insufficient_evidence'
                reason = "Insufficient evidence to determine notice alignment."
                
            for v in pa.get('vendors', []):
                doc_refs.extend(v.get('evidence_refs', []))
                
        elif test_name == 'check_consent_validity':
            consent_val = pa.get('consent_observation', {}).get('value', {})
            if not consent_val:
                state = 'insufficient_evidence'
                reason = "No consent observation data available."
            else:
                has_gap = False
                has_aligned = False
                for host, cstate in consent_val.items():
                    # If it fired pre-consent or ignores reject all, it's a gap
                    if cstate.get('pre_consent') or cstate.get('classification') == 'reject_only' or cstate.get('classification') == 'present_across_states':
                        has_gap = True
                    elif cstate.get('classification') == 'consent_dependent':
                        has_aligned = True
                        
                if has_gap:
                    state = 'gap'
                    reason = "Unconsented telemetry or persistent tracking across states observed."
                elif has_aligned:
                    state = 'aligned'
                    reason = "Consent gating observed to function correctly."
                else:
                    state = 'requires_human_review'
                    reason = "Mixed consent behavior requires manual review."
            tech_refs = pa.get('consent_observation', {}).get('evidence_refs', [])
            
        elif test_name == 'check_general_obligations':
            retention_status = pa.get('retention', {}).get('status', 'not_available')
            if retention_status == 'not_available':
                state = 'insufficient_evidence'
                reason = "Security, retention, and processor contract evidence not technically observable."
            else:
                state = 'requires_human_review'
                reason = "Requires manual review of contracts and safeguards."
                
        elif test_name == 'check_retention_mechanisms':
            state = 'insufficient_evidence'
            reason = "Retention mechanisms not observable from client side."
            
        elif test_name == 'check_lawful_basis':
            state = 'requires_human_review'
            reason = "Lawful basis determination requires contextual legal review."

        return ControlAssessment(
            assessment_id=f"LAW-{generate_id(pa.get('activity_id'), obs.rule_id)}",
            processing_activity_id=pa.get('activity_id'),
            rule_id=obs.rule_id,
            provision=obs.provision,
            legal_relevance="yes",
            current_enforceability=obs.commencement_status,
            readiness_assessment=state,
            current_legal_violation="not_assessed",
            technical_evidence_refs=list(set(tech_refs)),
            document_evidence_refs=list(set(doc_refs)),
            lineage_evidence_refs=[],
            reconciliation_refs=[f"RECON-{recon_status}"],
            reason=reason,
            confidence="high" if state in ['aligned', 'gap'] else "medium",
            requires_human_review=obs.human_review_required or state == 'requires_human_review'
        )
