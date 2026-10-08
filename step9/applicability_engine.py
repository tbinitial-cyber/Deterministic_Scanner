def evaluate_condition(condition: str, pa: dict) -> bool:
    if condition == 'processing_scope_is_in_scope':
        return True
    elif condition == 'notice_is_required':
        return True
    elif condition == 'relies_on_consent':
        return True
    elif condition == 'processing_involves_children':
        # Check if 'child' or 'children' is in data subject categories
        ds_cat = pa.get('data_subject_category', {}).get('value', '').lower()
        if 'child' in ds_cat: return True
        return False
    elif condition == 'sdf_status_is_active':
        # Defaulting to False without manual override
        return False
    elif condition == 'involves_foreign_transfer':
        # Check if cross_border is observed
        cb_obs = pa.get('cross_border_observation', {}).get('status', 'not_available')
        return cb_obs != 'not_available'
    
    return False

def get_applicable_obligations(pa: dict, obligations: list) -> list:
    applicable = []
    for obs in obligations:
        conditions_met = True
        for cond in obs.applies_when:
            if not evaluate_condition(cond, pa):
                conditions_met = False
                break
        if conditions_met:
            applicable.append(obs)
    return applicable
