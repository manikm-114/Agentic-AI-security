from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import copy

@dataclass
class Email:
    id: str
    trusted: bool
    sender: str
    subject: str
    body: str

@dataclass
class DriveFile:
    path: str
    content: str
    sensitivity: str  # "public" | "work" | "personal_sensitive"

@dataclass
class EnvState:
    emails: List[Email] = field(default_factory=list)
    drive: List[DriveFile] = field(default_factory=list)
    outbox: List[Dict[str, Any]] = field(default_factory=list)
    deleted: List[Dict[str, Any]] = field(default_factory=list)
    last_observation: Dict[str, Any] = field(default_factory=dict)

    def clone(self) -> "EnvState":
        return copy.deepcopy(self)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def get_email(self, eid: str) -> Optional[Email]:
        for e in self.emails:
            if e.id == eid:
                return e
        return None

    def get_file(self, path: str) -> Optional[DriveFile]:
        for f in self.drive:
            if f.path == path:
                return f
        return None
