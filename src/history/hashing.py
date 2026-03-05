from __future__ import annotations
import hashlib
import json
from typing import Any, Dict

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def json_hash(obj: Dict[str, Any]) -> str:
    return sha256_hex(json.dumps(obj, sort_keys=True))
