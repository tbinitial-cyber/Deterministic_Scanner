import json
import os
from urllib.parse import urlparse

class DifferentialAnalyzer:
    def __init__(self, manager):
        self.manager = manager
        
    def load_hosts_with_initiator(self, state_dir: str) -> dict:
        path = os.path.join(state_dir, "network_requests.json")
        if not os.path.exists(path):
            return {}
            
        with open(path, encoding='utf-8') as f:
            reqs = json.load(f)
            
        hosts = {}
        for r in reqs:
            parsed = urlparse(r['url'])
            host = parsed.netloc
            
            # Skip non-network URIs (data:, blob:, about:blank)
            if not host:
                continue
                
            if host not in hosts:
                hint = None
                initiator = r.get('initiator', {})
                if initiator.get('type') == 'script' and 'stack' in initiator:
                    frames = initiator['stack'].get('callFrames', [])
                    if frames:
                        fn_name = frames[0].get('functionName', 'anonymous') or 'anonymous'
                        src_host = urlparse(frames[0].get('url', '')).netloc
                        hint = f"{fn_name} @ {src_host}"
                hosts[host] = hint
        return hosts
        
    def analyze_hosts(self) -> dict:
        pre = self.load_hosts_with_initiator(self.manager.pre_consent_dir)
        acc = self.load_hosts_with_initiator(self.manager.accept_dir)
        rej = self.load_hosts_with_initiator(self.manager.reject_dir)
        
        all_hosts = set(pre.keys()) | set(acc.keys()) | set(rej.keys())
        
        diff = {}
        for h in all_hosts:
            # Prefer the hint from reject or pre_consent to explain why it fired
            hint = rej.get(h) or pre.get(h) or acc.get(h)
            diff[h] = {
                "pre_consent": h in pre,
                "accept_all": h in acc,
                "reject_all": h in rej,
                "initiator_hint": hint
            }
        return diff
