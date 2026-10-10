import hashlib

def generate_id(prefix: str, *args) -> str:
    hash_str = "-".join([str(a) for a in args]).encode()
    return f"{prefix}-{hashlib.md5(hash_str).hexdigest()[:8]}"

def derive_data_type_from_cookie(cookie_name: str) -> str:
    """Deterministically guess data type based on standard cookie name patterns, else unknown."""
    cookie_name = cookie_name.lower()
    if 'id' in cookie_name or 'uid' in cookie_name or '_ga' in cookie_name:
        return "tracking identifier / telemetry"
    if 'sess' in cookie_name or 'auth' in cookie_name or 'token' in cookie_name:
        return "session / authentication token"
    if 'consent' in cookie_name or 'opt' in cookie_name or 'eupub' in cookie_name:
        return "consent preference"
    return "unknown"

def get_consent_states(domain: str, behaviour_findings: list) -> dict:
    """Extracts consent state dict for a given domain from Step 2 findings."""
    for finding in behaviour_findings:
        if finding.get('target') == domain:
            return {
                'pre_consent_observed': finding.get('pre_consent', False),
                'accept_all_observed': finding.get('accept_all', False),
                'reject_all_attempted_observed': finding.get('reject_all', False)
            }
    return {}
