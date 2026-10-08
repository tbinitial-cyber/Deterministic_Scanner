from pydantic import BaseModel
from typing import Optional, List, Dict

class EnrichedHost(BaseModel):
    domain: str
    is_first_party: bool
    vendor: str
    category: str
    confidence: str
    consent_behavior: str
    initiator_hint: Optional[str] = None

class EnrichedCookie(BaseModel):
    name: str
    domain: str
    is_first_party: bool
    vendor: str
    category: str
    confidence: str

class DataFlowEdge(BaseModel):
    source: str
    target: str
    category: str
    consent_behavior: str

class DataFlowNode(BaseModel):
    id: str
    label: str
    type: str # 'client', 'first-party', 'third-party'
    category: str

class DataFlowGraph(BaseModel):
    nodes: List[DataFlowNode]
    edges: List[DataFlowEdge]
