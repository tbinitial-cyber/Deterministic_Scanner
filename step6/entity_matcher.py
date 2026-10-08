from .schemas import ProcessingEntity
from .normalizer import normalize_string

def match_entities(observed: list[ProcessingEntity], documented: list[ProcessingEntity]):
    results = []
    
    # 1. Compare Observed -> Documented
    for obs in observed:
        best_match_type = 'not_documented'
        best_doc = None
        matching_fields = []
        non_matching_fields = ['vendor', 'service', 'purpose']
        match_reason = "No matching documentation found."
        
        for doc in documented:
            v_obs = normalize_string(obs.vendor)
            v_doc = normalize_string(doc.vendor)
            s_obs = normalize_string(obs.service)
            s_doc = normalize_string(doc.service)
            
            if v_obs == v_doc and v_obs:
                if s_obs == s_doc:
                    best_match_type = 'matched'
                    best_doc = doc
                    matching_fields = ['vendor', 'service']
                    non_matching_fields = []
                    match_reason = "Exact vendor and service match."
                    break
                else:
                    best_match_type = 'ambiguous'
                    best_doc = doc
                    matching_fields = ['vendor']
                    non_matching_fields = ['service', 'purpose']
                    match_reason = "Vendor matches but explicitly different service identified."
                    
            elif v_doc == "broadcategory" and normalize_string(obs.category) == normalize_string(doc.category):
                if best_match_type == 'not_documented':
                    best_match_type = 'partial_match'
                    best_doc = doc
                    matching_fields = ['category']
                    non_matching_fields = ['vendor', 'service']
                    match_reason = "Broad wording category match."
                    
        results.append({
            'observed': obs,
            'documented': best_doc,
            'match_type': best_match_type,
            'matching_fields': matching_fields,
            'non_matching_fields': non_matching_fields,
            'match_reason': match_reason
        })
        
    # 2. Compare Documented -> Observed (Find Not Observed)
    for doc in documented:
        found = False
        for r in results:
            if r['documented'] and r['documented'].vendor == doc.vendor and r['documented'].service == doc.service:
                found = True
                break
        if not found:
            results.append({
                'observed': None,
                'documented': doc,
                'match_type': 'not_observed',
                'matching_fields': [],
                'non_matching_fields': ['vendor', 'service'],
                'match_reason': "Documented entity was not observed in live telemetry."
            })
            
    return results
