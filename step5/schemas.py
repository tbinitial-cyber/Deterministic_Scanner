from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

class ExtractedFact(BaseModel):
    value: str
    source_document: str
    section_hint: str
    snippet: str
    status: str  # 'extracted', 'not_found', 'requires_review'
    confidence: str  # 'high', 'medium', 'low'
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PolicyFact(BaseModel):
    data_categories: List[ExtractedFact] = Field(default_factory=list)
    purposes: List[ExtractedFact] = Field(default_factory=list)
    collection_methods: List[ExtractedFact] = Field(default_factory=list)
    third_parties: List[ExtractedFact] = Field(default_factory=list)
    retention_statements: List[ExtractedFact] = Field(default_factory=list)
    international_transfers: List[ExtractedFact] = Field(default_factory=list)
    rights_information: List[ExtractedFact] = Field(default_factory=list)
    cookie_disclosures: List[ExtractedFact] = Field(default_factory=list)

class DPAFact(BaseModel):
    processor_obligations: List[ExtractedFact] = Field(default_factory=list)
    subprocessors: List[ExtractedFact] = Field(default_factory=list)
    data_categories: List[ExtractedFact] = Field(default_factory=list)
    processing_purposes: List[ExtractedFact] = Field(default_factory=list)
    retention_deletion: List[ExtractedFact] = Field(default_factory=list)
    security_measures: List[ExtractedFact] = Field(default_factory=list)
    data_locations: List[ExtractedFact] = Field(default_factory=list)
    international_transfers: List[ExtractedFact] = Field(default_factory=list)
    transfer_mechanisms: List[ExtractedFact] = Field(default_factory=list)

class SubprocessorFact(BaseModel):
    vendor: ExtractedFact
    service: Optional[ExtractedFact] = None
    location: Optional[ExtractedFact] = None

class DocumentManifest(BaseModel):
    target_url: str
    documents_processed: dict  # filename -> sha256 hash
    extraction_timestamp: str
    extraction_engine: str
