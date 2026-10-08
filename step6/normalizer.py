import re

def normalize_string(s: str) -> str:
    if not s: return ""
    s = s.lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    for stop in ['llc', 'inc', 'ltd', 'corp', 'limited', 'group', 'technologies', 'software']:
        if s.endswith(stop):
            s = s[:-len(stop)]
    return s.strip()
