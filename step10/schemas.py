from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class RiskScenario(BaseModel):
    risk_id: str
    processing_activity_id: str
    risk_type: str
    description: str
    likelihood: int
    impact: int
    inherent_risk_score: int
    inherent_risk_level: str
    scoring_reason: List[str]
    technical_evidence_refs: List[str] = Field(default_factory=list)
    reconciliation_refs: List[str] = Field(default_factory=list)
    legal_refs: List[str] = Field(default_factory=list)

class ExistingControl(BaseModel):
    control_id: str
    processing_activity_id: str
    control_type: str
    description: str
    status: str
    effectiveness: str
    evidence_refs: List[str] = Field(default_factory=list)

class ResidualRisk(BaseModel):
    risk_id: str
    residual_likelihood: int
    residual_impact: int
    residual_risk_score: int
    residual_risk_level: str
    reduction_reason: List[str] = Field(default_factory=list)

class RemediationCandidate(BaseModel):
    remediation_id: str
    risk_id: str
    processing_activity_id: str
    remediation_type: str
    description: str
    priority: str

class DPIAssessment(BaseModel):
    assessment_id: str
    processing_activity_id: str
    processing_description: str
    purpose: str
    data_categories: List[str]
    data_subjects: str
    vendors: List[str]
    recipients: List[str]
    transfers: str
    automated_processing: str
    profiling: str
    consent_characteristics: str
    risk_factors: List[str]
    risk_scenarios: List[RiskScenario]
    existing_controls: List[ExistingControl]
    residual_risks: List[ResidualRisk]
    mitigations: List[RemediationCandidate]
    statutory_dpia_status: str
    requires_human_review: bool
    evidence_refs: List[str] = Field(default_factory=list)

class DPIAManifest(BaseModel):
    target_url: str
    timestamp: str
    input_hashes: Dict[str, str]
    output_hashes: Dict[str, str]
    total_assessments: int
    total_risks: int
