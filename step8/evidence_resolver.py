class EvidenceResolver:
    def __init__(self, step2_consent, step6_graph, step6_discrepancies, step7_nodes, step7_edges, step3_hosts):
        self.consent = step2_consent
        self.evidence_graph = step6_graph
        self.discrepancies = step6_discrepancies
        self.nodes = step7_nodes
        self.edges = step7_edges
        self.hosts = step3_hosts

    def get_hosts_for_vendor(self, vendor: str) -> list:
        if not vendor: return []
        return [h.get('domain') for h in self.hosts if h.get('vendor') == vendor and h.get('domain')]

    def get_consent_for_host(self, host: str) -> dict:
        for finding in self.consent:
            if finding.get('target') == host:
                return {
                    'pre_consent': finding.get('pre_consent'),
                    'accept_all': finding.get('accept_all'),
                    'reject_all': finding.get('reject_all'),
                    'classification': finding.get('classification')
                }
        return {}

    def get_reconciliation_status(self, vendor: str, service: str) -> str:
        # Check matched first
        for edge in self.evidence_graph:
            if edge.get('match_type') == 'matched':
                if edge['observed'] and edge['observed'].get('vendor') == vendor and edge['observed'].get('service') == service:
                    return 'matched'
                if edge['documented'] and edge['documented'].get('vendor') == vendor and edge['documented'].get('service') == service:
                    return 'matched'
        
        # Check discrepancies
        for disc in self.discrepancies:
            obs = disc.get('observed_entity')
            doc = disc.get('documented_entity')
            
            if obs and obs.get('vendor') == vendor and obs.get('service') == service:
                return disc.get('status', disc.get('type'))
            if doc and doc.get('vendor') == vendor and doc.get('service') == service:
                return disc.get('status', disc.get('type'))
                
        return 'unknown'

    def get_data_types_for_host(self, host: str) -> list:
        # Find host node
        host_node = next((n for n in self.nodes if n.get('node_type') == 'host' and n.get('name') == host), None)
        if not host_node: return []
        
        # Find associated cookies/storage via edges
        types = set()
        for e in self.edges:
            if e.get('source_node') == host_node.get('node_id') and e.get('relationship') == 'scoped_to':
                target_node = next((n for n in self.nodes if n.get('node_id') == e.get('target_node')), None)
                if target_node and target_node.get('data_type'):
                    types.add(target_node.get('data_type'))
                    
        return list(types)
