from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class ProposedAction:
    action: str
    tool: str
    args: Dict[str, Any]
    target: Dict[str, Any]
    reason: str
    ctx: Dict[str, Any]
