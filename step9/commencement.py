from datetime import datetime
import json
import yaml

def check_commencement(effective_from: str) -> str:
    # Just a simple deterministic checker against current system date
    # In reality, this would evaluate against commencement.yaml
    try:
        eff_date = datetime.strptime(effective_from, "%Y-%m-%d").date()
        today = datetime.now().date()
        if today >= eff_date:
            return "in_force"
        else:
            return "not_yet_in_force"
    except:
        return "unknown"

def inject_commencement(obligations: list) -> list:
    for obs in obligations:
        obs['commencement_status'] = check_commencement(obs.get('effective_from', ''))
    return obligations
