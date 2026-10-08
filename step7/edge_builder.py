from .schemas import LineageNode, LineageEdge
from .lineage_rules import generate_id, get_consent_states

class EdgeBuilder:
    def __init__(self, behaviour_findings):
        self.behaviour_findings = behaviour_findings
        
    def build_edges(self, nodes: list[LineageNode]) -> list[LineageEdge]:
        edges = []
        
        browser_node = next((n for n in nodes if n.node_type == 'browser'), None)
        cookie_nodes = [n for n in nodes if n.node_type == 'cookie']
        host_nodes = [n for n in nodes if n.node_type == 'host']
        service_nodes = [n for n in nodes if n.node_type == 'service']
        process_nodes = [n for n in nodes if n.node_type == 'logical_classification']
        
        if not browser_node: return edges
        
        # 1. Browser -> Host
        for host in host_nodes:
            cstates = get_consent_states(host.name, self.behaviour_findings)
            edges.append(LineageEdge(
                edge_id=generate_id('EDGE-sends', browser_node.node_id, host.node_id),
                source_node=browser_node.node_id,
                target_node=host.node_id,
                relationship="sends_to",
                consent_states=cstates if cstates else None,
                evidence_refs=host.evidence_refs + ["STEP2-CONSENT-MATRIX"],
                confidence="high"
            ))
            
            # 2. Host -> Service
            if host.vendor:
                for srv in service_nodes:
                    if srv.vendor == host.vendor:
                        edges.append(LineageEdge(
                            edge_id=generate_id('EDGE-resolves', host.node_id, srv.node_id),
                            source_node=host.node_id,
                            target_node=srv.node_id,
                            relationship="resolves_to",
                            evidence_refs=host.evidence_refs + srv.evidence_refs,
                            confidence="high"
                        ))
            
            # 3. Service -> Logical Classification
            if host.category:
                for proc in process_nodes:
                    if proc.name == host.category:
                        # Tie the service to the activity
                        for srv in service_nodes:
                            if srv.vendor == host.vendor:
                                edges.append(LineageEdge(
                                    edge_id=generate_id('EDGE-classifies', srv.node_id, proc.node_id),
                                    source_node=srv.node_id,
                                    target_node=proc.node_id,
                                    relationship="classified_as",
                                    evidence_refs=srv.evidence_refs + proc.evidence_refs,
                                    confidence="medium" # It's a DB lookup, not hard technical proof
                                ))
        
        # 4. Host -> Scoped To -> Cookie
        for cookie in cookie_nodes:
            # We map cookies to their domain scopes
            for host in host_nodes:
                if cookie.host.lstrip('.') in host.name or host.name in cookie.host:
                    edges.append(LineageEdge(
                        edge_id=generate_id('EDGE-scopes', host.node_id, cookie.node_id),
                        source_node=host.node_id,
                        target_node=cookie.node_id,
                        relationship="scoped_to",
                        evidence_refs=cookie.evidence_refs,
                        confidence="high"
                    ))
                    
            # 5. Cookie -> Stored In -> Browser
            edges.append(LineageEdge(
                edge_id=generate_id('EDGE-stores', cookie.node_id, browser_node.node_id),
                source_node=cookie.node_id,
                target_node=browser_node.node_id,
                relationship="stored_in",
                evidence_refs=cookie.evidence_refs,
                confidence="high"
            ))
            
        # Deduplicate edges just in case
        unique_edges = {e.edge_id: e for e in edges}
        return list(unique_edges.values())
