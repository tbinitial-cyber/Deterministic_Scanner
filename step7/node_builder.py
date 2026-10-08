from .schemas import LineageNode
from .lineage_rules import generate_id, derive_data_type_from_cookie

class NodeBuilder:
    def __init__(self, cookies, hosts, vendors):
        self.cookies = cookies
        self.hosts = hosts
        self.vendors = vendors
        
    def build_browser_node(self) -> LineageNode:
        return LineageNode(
            node_id="NODE-browser-01",
            node_type="browser",
            name="Browser / Client",
            data_type="unknown",
            source="Architecture Foundation",
            evidence_refs=["STEP1-BROWSER"]
        )
        
    def build_cookie_nodes(self) -> list[LineageNode]:
        nodes = []
        for c in self.cookies:
            cname = c.get('name', 'unknown')
            domain = c.get('domain', 'unknown')
            nodes.append(LineageNode(
                node_id=generate_id('NODE-cookie', cname, domain),
                node_type="cookie",
                name=cname,
                host=domain,
                data_type=derive_data_type_from_cookie(cname),
                source="Step 1 Telemetry",
                evidence_refs=[f"STEP1-COOKIE-{cname}"]
            ))
        return nodes
        
    def build_host_nodes(self) -> list[LineageNode]:
        nodes = []
        for h in self.hosts:
            domain = h.get('domain')
            if not domain: continue
            
            # Note: We do NOT invent the backend here. We just represent the endpoint.
            nodes.append(LineageNode(
                node_id=generate_id('NODE-host', domain),
                node_type="host",
                name=domain,
                host=domain,
                vendor=h.get('vendor'),
                category=h.get('category'),
                data_type="unknown", # We don't know the exact payload unless derived
                source="Step 3 Intelligence",
                evidence_refs=[f"STEP3-HOST-{domain}"]
            ))
        return nodes
        
    def build_service_nodes(self) -> list[LineageNode]:
        nodes = []
        for h in self.hosts:
            vendor = h.get('vendor')
            domain = h.get('domain')
            
            if not vendor or vendor == 'Unknown': continue
            
            service = domain.split('.')[0].capitalize() if domain else "Unknown Service"
            if 'clarity' in domain: service = 'Clarity'
            elif 'google' in domain or 'doubleclick' in domain: service = 'Google Ads/Analytics'
            
            node_id = generate_id('NODE-service', vendor, service)
            # Avoid duplicates
            if not any(n.node_id == node_id for n in nodes):
                nodes.append(LineageNode(
                    node_id=node_id,
                    node_type="service",
                    name=f"{vendor} {service}",
                    vendor=vendor,
                    service=service,
                    category=h.get('category'),
                    data_type="unknown",
                    source="Step 6 Processing Entities",
                    evidence_refs=[f"STEP6-ENTITY-{vendor}-{service}"]
                ))
        return nodes
        
    def build_processing_nodes(self) -> list[LineageNode]:
        nodes = []
        for h in self.hosts:
            cat = h.get('category')
            if not cat or cat == 'Unknown': continue
            
            node_id = generate_id('NODE-process', cat)
            if not any(n.node_id == node_id for n in nodes):
                nodes.append(LineageNode(
                    node_id=node_id,
                    node_type="logical_classification",
                    name=cat,
                    category=cat,
                    data_type="unknown",
                    source="Step 3 Intelligence DB Classification",
                    evidence_refs=[f"STEP3-CAT-{cat}"]
                ))
        return nodes
