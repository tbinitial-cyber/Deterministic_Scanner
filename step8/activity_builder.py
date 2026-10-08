import hashlib
from .schemas import ProcessingActivity, EvidenceField, VendorRecord

def generate_id(*args) -> str:
    return hashlib.md5("-".join([str(a) for a in args]).encode()).hexdigest()[:8]

class ActivityBuilder:
    def __init__(self, resolver):
        self.resolver = resolver
        
    def build_activity(self, category_name: str, entities: list) -> ProcessingActivity:
        
        # Gather all vendors for this activity
        vendors = []
        services = set()
        host_domains = set()
        evidence_refs = set()
        data_types = set()
        consent_obs = {}
        
        doc_status_priority = {
            'discrepant': 1, 
            'observed_entity_not_documented': 2,
            'ambiguous_processing_entity': 3, 
            'ambiguous': 4,
            'partial': 5, 
            'not_documented': 6, 
            'documented_entity_not_observed': 7,
            'not_observed': 8, 
            'matched': 9, 
            'unknown': 10
        }
        overall_doc_status = 'unknown'
        
        for e in entities:
            v_name = e.get('vendor')
            s_name = e.get('service')
            h_name = e.get('host')
            
            if s_name: services.add(s_name)
            if h_name: host_domains.add(h_name)
            for ref in e.get('evidence_refs', []):
                evidence_refs.add(ref)
                
            status = self.resolver.get_reconciliation_status(v_name, s_name)
            
            # Update overall status
            if doc_status_priority.get(status, 10) < doc_status_priority.get(overall_doc_status, 10):
                overall_doc_status = status
                
            observed = bool(e.get('source', '').startswith('Step 3') or e.get('source', '').startswith('Step 6'))
            
            # Consent and Data Types mapping
            # Only attach telemetry/consent hosts if the entity was actually observed
            v_hosts = []
            if observed:
                v_hosts = self.resolver.get_hosts_for_vendor(v_name)
            if h_name and h_name not in v_hosts: v_hosts.append(h_name)
            
            for h in v_hosts:
                host_domains.add(h)
                cstate = self.resolver.get_consent_for_host(h)
                if cstate: consent_obs[h] = cstate
                
                dtypes = self.resolver.get_data_types_for_host(h)
                data_types.update(dtypes)
                
            # If purely documented, ensure it has a Step 5 reference
            refs = e.get('evidence_refs', [])
            if not refs and e.get('source'):
                source_fmt = e.get('source').upper().replace(' ', '-')
                refs = [f"STEP5-POLICY-FACT-{source_fmt}"]
            for r in refs: evidence_refs.add(r)
                
            vendor_record = VendorRecord(
                vendor=v_name or "unknown",
                service=s_name or "unknown",
                host=h_name,
                role_if_documented="not_available", # Deferred to later logic
                purpose=e.get('purpose') or category_name,
                category=e.get('category') or category_name,
                observed=bool(e.get('source', '').startswith('Step 3') or e.get('source', '').startswith('Step 6')),
                documented=status in ['matched', 'ambiguous', 'partial', 'not_observed'],
                reconciliation_status=status,
                evidence_refs=refs
            )
            vendors.append(vendor_record)
            
        data_cats = list(data_types) if data_types else ["unknown"]
        
        return ProcessingActivity(
            activity_id=f"PA-{generate_id(category_name)}",
            activity_name=category_name.title(),
            purpose=EvidenceField(value=category_name, status="derived", evidence_refs=list(evidence_refs)[:3]),
            data_categories=EvidenceField(value=data_cats, status="observed" if "unknown" not in data_cats else "unknown", evidence_refs=list(evidence_refs)[:3]),
            data_elements=EvidenceField(value="not_available", status="not_available"),
            data_subject_category=EvidenceField(value="website visitor", status="derived"),
            source=EvidenceField(value="browser", status="observed", evidence_refs=["STEP1-BROWSER"]),
            collection_channel=EvidenceField(value="network request", status="observed"),
            vendors=vendors,
            services=list(services),
            recipients=[v.vendor for v in vendors],
            host_domains=list(host_domains),
            processing_category=EvidenceField(value=category_name, status="derived"),
            consent_observation=EvidenceField(value=consent_obs, status="observed", evidence_refs=["STEP2-CONSENT-MATRIX"]),
            cross_border_observation=EvidenceField(value="not_available", status="not_available"),
            retention=EvidenceField(value="not_available", status="not_available"),
            documentation_status=overall_doc_status,
            evidence_refs=list(evidence_refs),
            source_refs=[],
            confidence="high" if any(v.observed for v in vendors) else "medium",
            status="draft",
            requires_review=True
        )
