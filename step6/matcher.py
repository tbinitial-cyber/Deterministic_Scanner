from .schemas import MatchedEntity
from .normalizer import contains_concept

def match_entities(observed_list, documented_list, broad_wording_hints: dict = None) -> list[MatchedEntity]:
    matches = []
    obs_map = {o.normalized_value: o for o in observed_list}
    doc_map = {d.normalized_value: d for d in documented_list}
    
    all_keys = set(obs_map.keys()) | set(doc_map.keys())
    for k in all_keys:
        obs = obs_map.get(k)
        doc = doc_map.get(k)
        
        match_type = 'unknown'
        
        if obs and doc:
            match_type = 'matched'
        elif obs and not doc:
            # Check if broad wording covers it (e.g., 'Google' not explicitly named, but 'analytics providers' is used)
            broad_match = False
            if broad_wording_hints and obs.entity_type in broad_wording_hints:
                # We simulate checking if the broad wording is present in the document snippets
                # This logic is handled at the runner level, so if it reaches here, it's truly undocumented
                pass
            match_type = 'not_documented'
        elif doc and not obs:
            match_type = 'not_observed'
            
        matches.append(MatchedEntity(
            entity_type=obs.entity_type if obs else doc.entity_type,
            normalized_value=k,
            observed=obs,
            documented=doc,
            match_type=match_type
        ))
        
    return matches
