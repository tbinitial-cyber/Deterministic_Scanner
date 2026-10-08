def group_activities(nodes: list, evidence_graph: list) -> dict:
    """
    Groups entities into discrete Processing Activities based on Category/Purpose.
    Returns: Dict[category_name, List[ProcessingEntity]]
    """
    groups = {}
    
    # 1. Group from Live Reality (Step 7 Nodes)
    for n in nodes:
        if n.get('node_type') == 'service':
            cat = n.get('category') or n.get('purpose')
            if not cat or cat == 'Unknown': cat = 'Unclassified Processing'
            
            if cat not in groups:
                groups[cat] = []
            
            # Avoid duplicates
            if not any(x.get('vendor') == n.get('vendor') and x.get('service') == n.get('service') for x in groups[cat]):
                groups[cat].append(n)
                
    # 2. Add Documented entities from Step 6 (Not Observed OR Ambiguous)
    for edge in evidence_graph:
        doc = edge.get('documented')
        obs = edge.get('observed')
        match_type = edge.get('match_type')
        
        # If it's completely unobserved, or if it matched the vendor but the service/purpose is explicitly different (ambiguous)
        if doc and (not obs or match_type == 'ambiguous'):
            cat = doc.get('purpose') or doc.get('category') or 'Documented Processing'
            if cat not in groups:
                groups[cat] = []
                
            if not any(x.get('vendor') == doc.get('vendor') and x.get('service') == doc.get('service') for x in groups[cat]):
                groups[cat].append(doc)
                
    return groups
