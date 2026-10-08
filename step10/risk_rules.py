def calculate_level(score: int) -> str:
    if score <= 4: return "low"
    if score <= 9: return "medium"
    if score <= 16: return "high"
    return "critical"

def evaluate_risk_factors(pa: dict, legal: list) -> list:
    factors = []
    
    # 1. Behavioural Tracking
    purpose = pa.get('purpose', {}).get('value', '').lower()
    cat = pa.get('processing_category', {}).get('value', '').lower()
    if 'behavioural' in purpose or 'tracking' in purpose or 'analytics' in cat or 'advertising' in cat:
        factors.append("tracking / behavioural analytics")
        
    # 2. Third-party risk
    vendors = pa.get('vendors', [])
    if any(not v.get('vendor', '').lower().startswith('first-party') for v in vendors):
        factors.append("multiple third parties")
        
    # 3. Documentation mismatch
    recon = pa.get('documentation_status', 'unknown')
    if recon in ['not_documented', 'ambiguous', 'partial', 'observed_entity_not_documented', 'ambiguous_processing_entity']:
        factors.append("consent/documentation mismatch")
        
    # 4. Unknown Retention
    if pa.get('retention', {}).get('status') == 'not_available':
        factors.append("retention uncertainty")
        
    # 5. Security Uncertainty (if S8 is missing)
    for l in legal:
        if l['rule_id'] == 'DPDPA_S8_GENERAL' and l['readiness_assessment'] == 'insufficient_evidence':
            factors.append("security-control uncertainty")
            
    return list(set(factors))
