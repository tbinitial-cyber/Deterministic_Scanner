from pydantic import BaseModel
from typing import Optional

class Finding(BaseModel):
    target: str
    category: str  # 'host', 'cookie', etc.
    pre_consent: bool
    accept_all: bool
    reject_all: bool
    classification: str
    initiator_hint: Optional[str] = None
