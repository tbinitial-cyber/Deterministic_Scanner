from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LineageNode(BaseModel):
    node_id: str
    node_type: str  # browser, cookie, storage, request, endpoint, host, vendor, service, processing_activity, database, table, column, transformation, derived_data
    name: str
    vendor: Optional[str] = None
    service: Optional[str] = None
    host: Optional[str] = None
    data_type: str = "unknown"
    purpose: Optional[str] = None
    category: Optional[str] = None
    role: Optional[str] = None
    source: str
    evidence_refs: List[str] = Field(default_factory=list)

class LineageEdge(BaseModel):
    edge_id: str
    source_node: str
    target_node: str
    relationship: str  # collects, sets, sends_to, calls, receives, stores, transforms, derives, shares_with, resolves_to, performs
    direction: str = "directed"
    consent_states: Optional[Dict[str, bool]] = None
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: str

class LineageGraph(BaseModel):
    nodes: List[LineageNode]
    edges: List[LineageEdge]

class LineageManifest(BaseModel):
    target_url: str
    timestamp: str
    input_hashes: Dict[str, str]
    output_hashes: Dict[str, str]
    total_nodes: int
    total_edges: int
