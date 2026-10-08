from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class EvidenceField(BaseModel):
    value: Any
    status: str
    evidence_refs: List[str] = Field(default_factory=list)

class VendorRecord(BaseModel):
    vendor: str
    service: str
    host: Optional[str] = None
    role_if_documented: str = "unknown"
    purpose: str = "unknown"
    category: str = "unknown"
    observed: bool = False
    documented: bool = False
    reconciliation_status: str = "unknown"
    evidence_refs: List[str] = Field(default_factory=list)

class ProcessingActivity(BaseModel):
    activity_id: str
    activity_name: str
    description: str = "not_available"
    purpose: EvidenceField
    data_categories: EvidenceField
    data_elements: EvidenceField
    data_subject_category: EvidenceField
    source: EvidenceField
    collection_channel: EvidenceField
    vendors: List[VendorRecord] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    recipients: List[str] = Field(default_factory=list)
    host_domains: List[str] = Field(default_factory=list)
    processing_category: EvidenceField
    consent_observation: EvidenceField
    cross_border_observation: EvidenceField
    storage_location: str = "not_available"
    retention: EvidenceField
    automated_processing: str = "not_available"
    derived_data: str = "not_available"
    documentation_status: str = "unknown"
    evidence_refs: List[str] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list)
    confidence: str = "medium"
    status: str = "draft"
    requires_review: bool = True

class RopaManifest(BaseModel):
    target_url: str
    timestamp: str
    input_hashes: Dict[str, str]
    output_hashes: Dict[str, str]
    total_activities: int
    total_vendors: int
