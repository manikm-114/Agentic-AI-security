from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class PermissionProfile:
    name: str
    rules: Dict[str, Any]

    def allows(self, action: str, resource: Dict[str, Any]) -> bool:
        spec = self.rules.get(action)
        if spec is None:
            return False
        if spec == "ALL":
            return True

        rtype = resource.get("type")
        if rtype == "email":
            return bool(spec.get("email", False))

        if rtype == "drive":
            path = resource.get("path", "")
            prefixes = spec.get("drive_prefixes", [])
            return any(path.startswith(p) for p in prefixes)

        if rtype == "email_send":
            return bool(spec.get("email", False))

        return False

    def snapshot(self) -> Dict[str, Any]:
        return {"name": self.name, "rules": self.rules}
