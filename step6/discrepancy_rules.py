import hashlib
import json
import os
from .schemas import Discrepancy

def generate_id(*args) -> str:
    return hashlib.md5("-".join([str(a) for a in args]).encode()).hexdigest()[:8]

def evaluate_results(match_results: list, dpa_path: str) -> list[Discrepancy]:
    discs = []
    
    for res in match_results:
        mtype = res['match_type']
        obs = res['observed']
        doc = res['documented']
        
        if mtype == 'ambiguous':
            discs.append(Discrepancy(
                finding_id=f"REC-{generate_id('ambiguous', obs.vendor, obs.service)}",
                type="ambiguous_processing_entity",
                observed_entity=obs,
                documented_entity=doc,
                technical_evidence=f"Observed service {obs.service} via {obs.host}",
                document_evidence=f"Documentation claims {doc.service}",
                matching_fields=res['matching_fields'],
                non_matching_fields=res['non_matching_fields'],
                match_reason=res['match_reason'],
                confidence="high",
                requires_review=True
            ))
        elif mtype == 'not_documented':
            discs.append(Discrepancy(
                finding_id=f"REC-{generate_id('not_documented', obs.vendor, obs.service)}",
                type="observed_entity_not_documented",
                observed_entity=obs,
                documented_entity=None,
                technical_evidence=f"Observed service {obs.service} via {obs.host}",
                document_evidence="No specific or broad documentation found.",
                matching_fields=[],
                non_matching_fields=['vendor', 'service'],
                match_reason=res['match_reason'],
                confidence="high",
                requires_review=True
            ))
        elif mtype == 'not_observed':
            discs.append(Discrepancy(
                finding_id=f"REC-{generate_id('not_observed', doc.vendor, doc.service)}",
                type="documented_entity_not_observed",
                observed_entity=None,
                documented_entity=doc,
                technical_evidence="Telemetry did not trigger this vendor/service.",
                document_evidence=f"Documentation explicitly lists {doc.vendor} {doc.service}",
                matching_fields=[],
                non_matching_fields=['vendor', 'service'],
                match_reason=res['match_reason'],
                confidence="medium",
                requires_review=False
            ))
        elif mtype == 'partial_match':
            discs.append(Discrepancy(
                finding_id=f"REC-{generate_id('partial', obs.vendor, obs.service)}",
                type="broad_wording_partial_match",
                observed_entity=obs,
                documented_entity=doc,
                technical_evidence=f"Observed explicit vendor {obs.vendor}",
                document_evidence="Policy uses broad category language rather than explicit vendor naming.",
                matching_fields=res['matching_fields'],
                non_matching_fields=res['non_matching_fields'],
                match_reason=res['match_reason'],
                confidence="medium",
                requires_review=True
            ))
            
    # DPA Check
    dpa = {}
    if os.path.exists(dpa_path):
        with open(dpa_path, encoding='utf-8') as f:
            dpa = json.load(f)
    if not dpa.get('customer_role'):
        discs.append(Discrepancy(
            finding_id=f"REC-{generate_id('missing_dpa')}",
            type="document_not_discovered",
            observed_entity=None,
            documented_entity=None,
            technical_evidence="N/A",
            document_evidence="No DPA found in searched sources.",
            matching_fields=[],
            non_matching_fields=[],
            match_reason="DPA not discovered in Step 5 crawler.",
            confidence="high",
            requires_review=True
        ))
        
    return discs
