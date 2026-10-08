from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class NetworkRequest(BaseModel):
    request_id: str
    url: str
    method: str
    resource_type: str = Field(default="")
    timestamp: float
    headers: Dict[str, Any]
    initiator: Dict[str, Any] = Field(default_factory=dict)

class NetworkResponse(BaseModel):
    request_id: str
    url: str
    status: int
    mime_type: str = Field(default="")
    timestamp: float
    headers: Dict[str, Any]

class NetworkLoadingFinished(BaseModel):
    request_id: str
    timestamp: float
    encoded_data_length: float

class NetworkLoadingFailed(BaseModel):
    request_id: str
    timestamp: float
    error_text: str
    canceled: bool = False

class Cookie(BaseModel):
    name: str
    value: str
    domain: str
    path: str
    expires: float
    httpOnly: bool
    secure: bool
    sameSite: str

class StorageItem(BaseModel):
    storage_type: str  # 'localStorage' or 'sessionStorage'
    key: str
    value: str

class ScanManifest(BaseModel):
    target_url: str
    captured_at: str
    files: Dict[str, str]  # filename -> sha256 hash
