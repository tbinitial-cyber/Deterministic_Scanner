import os

class StateManager:
    def __init__(self, base_dir="output/consent_audit"):
        self.base_dir = base_dir
        self.pre_consent_dir = os.path.join(base_dir, "pre_consent")
        self.accept_dir = os.path.join(base_dir, "accept_all")
        self.reject_dir = os.path.join(base_dir, "reject_all")
        
    def setup(self):
        os.makedirs(self.pre_consent_dir, exist_ok=True)
        os.makedirs(self.accept_dir, exist_ok=True)
        os.makedirs(self.reject_dir, exist_ok=True)
