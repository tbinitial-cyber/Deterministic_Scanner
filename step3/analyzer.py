import json
import os
import tldextract
from urllib.parse import urlparse
from .schemas import EnrichedHost, EnrichedCookie, DataFlowGraph, DataFlowNode, DataFlowEdge

class IntelligenceAnalyzer:
    def __init__(self, target_url: str, base_dir="output", db_path="step3/intelligence_db.json"):
        self.target_url = target_url
        self.base_dir = base_dir

        if db_path == "step3/intelligence_db.json":
            db_path = os.path.join(os.path.dirname(__file__), "intelligence_db.json")

        with open(db_path, encoding='utf-8') as f:
            self.db = json.load(f)

        target_hostname = urlparse(target_url).netloc
        self.extractor = tldextract.TLDExtract(suffix_list_urls=())
        self.target_ext = self.extractor(self.normalize_hostname(target_hostname))

    def normalize_hostname(self, host: str) -> str:
        """Normalize case and trailing dots, parsing safely."""
        if not host:
            return ""
        # If a URL is passed instead of just a host, extract the netloc
        if "://" in host:
            host = urlparse(host).netloc
        return host.strip().rstrip('.').lower()

    def is_first_party(self, host: str) -> bool:
        """
        Check if a host shares the same registrable domain as the target.
        Note: Matching registrable domains establishes a technical domain boundary relationship,
        it does not prove common corporate ownership.
        IP addresses like 127.0.0.1 and 'localhost' are treated strictly by their string representation.
        """
        norm_host = self.normalize_hostname(host)
        host_ext = self.extractor(norm_host)
        host_registered = f"{host_ext.domain}.{host_ext.suffix}"
        target_registered = f"{self.target_ext.domain}.{self.target_ext.suffix}"
        return host_registered == target_registered

    def resolve_host(self, host: str) -> dict:
        if self.is_first_party(host):
            return {"vendor": "First-party", "category": "Core application", "confidence": "high"}

        norm_host = self.normalize_hostname(host)
        for db_host, info in self.db.get("hosts", {}).items():
            db_norm = self.normalize_hostname(db_host)
            if norm_host == db_norm or norm_host.endswith("." + db_norm):
                return info

        return {"vendor": "Unknown", "category": "Other / Unknown", "confidence": "low"}

    def resolve_cookie(self, name: str, domain: str) -> dict:
        if self.is_first_party(domain):
            vendor_default = "First-party"
        else:
            vendor_default = "Unknown third-party"

        for db_cookie, info in self.db.get("cookies", {}).items():
            if db_cookie == name or (db_cookie.startswith("_") and name.startswith(db_cookie)):
                # Exact match or prefix match for analytics cookies like _ga_XXXX
                return info

        return {"vendor": vendor_default, "category": "Other / Unknown", "confidence": "low"}

    def analyze_hosts(self) -> tuple[list[EnrichedHost], DataFlowGraph]:
        findings_path = os.path.join(self.base_dir, "consent_audit", "behaviour_findings.json")
        if not os.path.exists(findings_path):
            raise FileNotFoundError("Step 2 behaviour_findings.json not found.")

        with open(findings_path, encoding='utf-8') as f:
            findings = json.load(f)

        enriched_hosts = []
        nodes = [DataFlowNode(id="Browser", label="User Browser", type="client", category="Client")]
        edges = []

        for f in findings:
            host = f['target']
            intel = self.resolve_host(host)

            eh = EnrichedHost(
                domain=host,
                normalized_domain=self.normalize_hostname(host),
                is_first_party=self.is_first_party(host),
                vendor=intel['vendor'],
                category=intel['category'],
                confidence=intel['confidence'],
                consent_behavior=f['classification'],
                initiator_hint=f.get('initiator_hint')
            )
            enriched_hosts.append(eh)

            node_type = "first-party" if eh.is_first_party else "third-party"
            nodes.append(DataFlowNode(id=host, label=eh.vendor, type=node_type, category=eh.category))

            edges.append(DataFlowEdge(
                source="Browser",
                target=host,
                category=eh.category,
                consent_behavior=eh.consent_behavior
            ))

        return enriched_hosts, DataFlowGraph(nodes=nodes, edges=edges)

    def analyze_cookies(self) -> list[EnrichedCookie]:
        # We take the accept_all snapshot as the most complete reality
        cookies_path = os.path.join(self.base_dir, "consent_audit", "accept_all", "cookies.json")
        if not os.path.exists(cookies_path):
            return []

        with open(cookies_path, encoding='utf-8') as f:
            raw_cookies = json.load(f)

        enriched_cookies = []
        for c in raw_cookies:
            intel = self.resolve_cookie(c['name'], c['domain'])
            enriched_cookies.append(EnrichedCookie(
                name=c['name'],
                domain=c['domain'],
                is_first_party=self.is_first_party(c['domain']),
                vendor=intel['vendor'],
                category=intel['category'],
                confidence=intel['confidence']
            ))
        return enriched_cookies
