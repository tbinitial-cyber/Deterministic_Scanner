import json
from .schemas import ProcessingEntity

class GraphBuilder:
    def __init__(self, step3_path: str, step5_path: str):
        self.step3_path = step3_path
        self.step5_path = step5_path
        
    def build_observed(self) -> list[ProcessingEntity]:
        with open(f"{self.step3_path}/hosts.json", encoding='utf-8') as f:
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
        with open(f"{self.step5_path}/policy_facts.json", encoding='utf-8') as f:
            policy = json.load(f)
            
        documented = []
        snips = [item.get('snippet', '') for item in policy.get('third_parties', [])]
        text = " ".join(snips).lower()
        
        # Deterministically extract known structured relationships based on policy text
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
            
        
        return documented
