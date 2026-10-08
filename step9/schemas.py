from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LegalObligation(BaseModel):
    rule_id: str
    source_type: str
    source_document: str
    provision: str
    title: str
    requirement: List[str]
    applies_when: List[str]
    effective_from: str
    commencement_status: str = "unknown"
    exceptions: List[str] = Field(default_factory=list)
    evidence_required: List[str]
    technical_test: str
    possible_outcomes: List[str]
    human_review_required: bool

class ControlAssessment(BaseModel):
    assessment_id: str
    processing_activity_id: str
    rule_id: str
    provision: str
    legal_relevance: str = "yes"
    current_enforceability: str
    readiness_assessment: str
    current_legal_violation: str = "not_assessed"
    technical_evidence_refs: List[str] = Field(default_factory=list)
    document_evidence_refs: List[str] = Field(default_factory=list)
    lineage_evidence_refs: List[str] = Field(default_factory=list)
    reconciliation_refs: List[str] = Field(default_factory=list)
    reason: str
    confidence: str
    requires_human_review: bool

class LegalManifest(BaseModel):
    target_url: str
    timestamp: str
    input_hashes: Dict[str, str]
    output_hashes: Dict[str, str]
    total_assessments: int
