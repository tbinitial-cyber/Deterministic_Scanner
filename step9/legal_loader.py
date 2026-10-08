import os
import yaml
from .schemas import LegalObligation

def load_knowledge_base(legal_dir: str) -> list[LegalObligation]:
    obligations = []
    for filename in ['dpdpa_obligations.yaml', 'dpdp_rules.yaml']:
        path = os.path.join(legal_dir, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or []
                for item in data:
                    obligations.append(LegalObligation(**item))
    return obligations
