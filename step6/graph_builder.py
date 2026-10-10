import json
import os
from .schemas import ProcessingEntity

class GraphBuilder:
    def __init__(self, step3_path: str, step5_path: str):
        self.step3_path = step3_path
        self.step5_path = step5_path

    def build_observed(self) -> list[ProcessingEntity]:
        hosts_path = f"{self.step3_path}/hosts.json"
        if not os.path.exists(hosts_path):
            raise FileNotFoundError(f"Missing technical prerequisite: {hosts_path} was not found. Please run Step 3 (Data Flow Intelligence) first.")

        with open(hosts_path, encoding='utf-8') as f:
            hosts = json.load(f)

        observed = []
        for h in hosts:
            if h.get('is_first_party'): continue
            vendor = h.get('vendor')
            if vendor == 'Unknown': continue

            domain = h.get('domain')
            category = h.get('category')

            # Deterministically derive service from domain mapping logic
            service = domain.split('.')[0].capitalize() if domain else None
            if 'clarity' in domain: service = 'Clarity'
            elif 'google' in domain or 'doubleclick' in domain: service = 'Google Ads/Analytics'
            elif 'onetrust' in domain or 'cookielaw' in domain: service = 'Cookie Consent'
            elif 'intercom' in domain: service = 'Messenger'

            observed.append(ProcessingEntity(
                vendor=vendor,
                service=service,
                host=domain,
                purpose=category,
                category=category,
                source=f"Step 3 Telemetry ({domain})"
            ))
        return observed

    def build_documented(self) -> list[ProcessingEntity]:
        policy_path = f"{self.step5_path}/policy_facts.json"
        if not os.path.exists(policy_path):
            return []

        with open(policy_path, encoding='utf-8') as f:
            policy = json.load(f)

        documented = []

        cookie_snippets = []
        has_subprocessor_ref = False

        for section, items in policy.items():
            for item in items:
                if item.get('status') == 'extracted':
                    snip = item.get('snippet', '')
                    lower_snip = snip.lower()
                    if 'cookie' in lower_snip or 'tracker' in lower_snip:
                        cookie_snippets.append(snip)
                    if 'subprocessor' in lower_snip:
                        has_subprocessor_ref = True

        if cookie_snippets:
            documented.append(ProcessingEntity(
                vendor="Broad Category",
                service="Cookies and Trackers",
                purpose="Tracking",
                category="Tracking",
                source="Privacy Policy (Cross-section)"
            ))

        if has_subprocessor_ref:
            documented.append(ProcessingEntity(
                vendor="Unresolved Reference",
                service="Subprocessors",
                purpose="Vendor Processing",
                source="Privacy Policy Reference"
            ))

        snips = [item.get('snippet', '') for item in policy.get('third_parties', []) if item.get('status') == 'extracted']
        text = " ".join(snips).lower()

        if 'microsoft' in text and 'ai' in text:
            documented.append(ProcessingEntity(
                vendor="Microsoft",
                service="Azure OpenAI",
                purpose="AI features",
                source="Privacy Policy"
            ))

        if 'analytics' in text:
            documented.append(ProcessingEntity(
                vendor="Broad Category",
                service="Analytics Vendors",
                purpose="Analytics",
                category="Analytics",
                source="Privacy Policy"
            ))

        sub_path = f"{self.step5_path}/subprocessors.json"
        if os.path.exists(sub_path):
            with open(sub_path, encoding='utf-8') as f:
                subs = json.load(f)
            for sub in subs:
                vendor = sub.get('name')
                if vendor:
                    documented.append(ProcessingEntity(
                        vendor=vendor,
                        service=sub.get('purpose', 'Subprocessing'),
                        purpose=sub.get('purpose'),
                        source="Subprocessor List"
                    ))

        return documented
