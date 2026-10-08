from pydantic import BaseModel
from typing import List, Optional, Dict

class ProcessingEntity(BaseModel):
    vendor: Optional[str] = None
    service: Optional[str] = None
    host: Optional[str] = None
    purpose: Optional[str] = None
    category: Optional[str] = None
    data_type: Optional[str] = None
    role: Optional[str] = None
    source: str

class Discrepancy(BaseModel):
    finding_id: str
    type: str
    observed_entity: Optional[ProcessingEntity] = None
    documented_entity: Optional[ProcessingEntity] = None
    technical_evidence: str
    document_evidence: str
    matching_fields: List[str]
    non_matching_fields: List[str]
    match_reason: str
    confidence: str
    requires_review: bool

class ReconciliationManifest(BaseModel):
    target_url: str
    timestamp: str
    input_hashes: Dict[str, str]
    output_hashes: Dict[str, str]
    total_observed: int
    total_documented: int
    total_matched: int
    total_discrepancies: int
