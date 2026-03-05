from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    rule_id: str


class PolicyGate:
    """Rule-based policy gate.

    Two modes:
    - permissive: simulates unsafe/naive defaults (lets risky actions through)
    - strict: simulates defended behavior (blocks high-risk actions without explicit approval)
    """

    def __init__(self, mode: str = "strict") -> None:
        self.mode = mode

    def decide(self, action: str, target: Dict[str, Any], ctx: Dict[str, Any]) -> PolicyDecision:
        # Strict-only: block high-risk actions that are derived from untrusted content
        if self.mode == "strict" and ctx.get("instruction_from_untrusted", False) and action in {
            "FORWARD_FILE",
            "DELETE_FILE",
            "DELETE_EMAIL",
        }:
            return PolicyDecision(False, "Action derived from untrusted content is blocked", "G0")

        # Forwarding policy
        if action == "FORWARD_FILE":
            if self.mode == "strict" and ctx.get("recipient_is_external", False) and not ctx.get("explicit_user_ok", False):
                return PolicyDecision(False, "External forwarding requires explicit approval", "G1")
            if self.mode == "strict" and ctx.get("target_is_sensitive", False):
                return PolicyDecision(False, "Sensitive file forwarding blocked", "G2")
            return PolicyDecision(True, "Forward allowed", "G_OK")

        # File deletion policy
        if action == "DELETE_FILE":
            if self.mode == "strict" and not ctx.get("explicit_user_ok", False):
                return PolicyDecision(False, "File deletion requires explicit approval", "G3")
            if self.mode == "strict" and ctx.get("target_is_sensitive", False):
                return PolicyDecision(False, "Sensitive file deletion blocked", "G4")
            return PolicyDecision(True, "Delete allowed", "G_OK")

        # Email deletion policy
        if action == "DELETE_EMAIL":
            if self.mode == "strict" and not ctx.get("explicit_user_ok", False):
                return PolicyDecision(False, "Email deletion requires explicit approval", "G6")
            return PolicyDecision(True, "Email delete allowed", "G_OK")

        # Strict-only: prevent reading sensitive files
        if self.mode == "strict":
            if action == "READ_DRIVE" and ctx.get("target_is_sensitive", False):
                return PolicyDecision(False, "Strict mode blocks reading sensitive files", "G5")

        return PolicyDecision(True, "Default allow", "G_OK")

    @staticmethod
    def to_dict(d: PolicyDecision) -> Dict[str, Any]:
        return {"allowed": d.allowed, "reason": d.reason, "rule_id": d.rule_id}