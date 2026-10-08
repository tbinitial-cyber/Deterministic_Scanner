from .schemas import Finding

def generate_findings(diff_hosts: dict) -> list[Finding]:
    findings = []
    for host, presence in diff_hosts.items():
        pre = presence['pre_consent']
        acc = presence['accept_all']
        rej = presence['reject_all']
        
        if pre and acc and rej:
            classification = "present_across_states"
        elif not pre and acc and not rej:
            classification = "consent_dependent"
        elif pre and rej and not acc:
            classification = "inconsistent_absence"
        elif not pre and rej and not acc:
            classification = "reject_only"
        elif not pre and acc and rej:
            classification = "post_action_dependent"
        else:
            classification = "mixed_behavior"
            
        findings.append(Finding(
            target=host,
            category="host",
            pre_consent=pre,
            accept_all=acc,
            reject_all=rej,
            classification=classification,
            initiator_hint=presence.get('initiator_hint')
        ))
    return findings
