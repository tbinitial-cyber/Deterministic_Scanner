import hashlib
import json
import os
from typing import Union, List
from pydantic import BaseModel

def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def save_json(data: Union[List[BaseModel], BaseModel, dict, list], filepath: str):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], BaseModel):
            json.dump([item.model_dump() for item in data], f, indent=2)
        elif isinstance(data, BaseModel):
            json.dump(data.model_dump(), f, indent=2)
        else:
            json.dump(data, f, indent=2)
