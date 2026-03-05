from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.agent.planner import Planner
from src.agent.actions import ProposedAction
from src.env.state import EnvState
from src.defenses.permissions import PermissionProfile
from src.defenses.policy_gate import PolicyGate
from src.history.verilog import VeriLog
from src.history.hashing import json_hash


@dataclass
class StepRecord:
    step: int
    proposal: Dict[str, Any]
    decision: Dict[str, Any]
    result: Dict[str, Any]
    env_hash: str


class ToolAgent:
    def __init__(self, planner: Planner) -> None:
        self.planner = planner

    def run(
        self,
        env: EnvState,
        task: Dict[str, Any],
        profile: PermissionProfile,
        gate: PolicyGate,
        use_audit: bool = True,
        step_limit: int = 10,
    ) -> Tuple[List[StepRecord], Optional[VeriLog]]:
        log = VeriLog() if use_audit else None
        trace: List[StepRecord] = []

        for step in range(step_limit):
            pa = self.planner.next_action(env, task, step)
            if pa is None:
                break

            # Permissions: resource-level allow/deny
            perm_ok = profile.allows(pa.action, pa.target)

            # Policy: semantic allow/deny
            pdec = gate.decide(pa.action, pa.target, pa.ctx)
            allowed = bool(perm_ok and pdec.allowed)

            decision = {
                "allowed": allowed,
                "perm_ok": perm_ok,
                **gate.to_dict(pdec),
            }

            # Execute tool if allowed
            result = {"ok": False}
            if allowed:
                result = self._execute(env, pa)

            h = json_hash(env.to_dict())

            # Audit append
            if log is not None:
                log.append(
                    action=pa.action,
                    tool=pa.tool,
                    args=pa.args,
                    result=result,
                    decision=decision,
                    permissions_snapshot=profile.snapshot(),
                    env_hash=h,
                )

            trace.append(
                StepRecord(
                    step=step,
                    proposal={
                        "action": pa.action,
                        "tool": pa.tool,
                        "args": pa.args,
                        "target": pa.target,
                        "reason": pa.reason,
                        "ctx": pa.ctx,
                    },
                    decision=decision,
                    result=result,
                    env_hash=h,
                )
            )

        return trace, log

    def _execute(self, env: EnvState, pa: ProposedAction) -> Dict[str, Any]:
        # Minimal tool implementations for the offline simulator
        if pa.tool == "email.read":
            e = env.get_email(pa.args["id"])
            env.last_observation = {
                "email": None
                if e is None
                else {
                    "id": e.id,
                    "trusted": e.trusted,
                    "from": e.sender,
                    "subject": e.subject,
                    "body": e.body,
                }
            }
            return {"ok": True, "email_found": e is not None}

        if pa.tool == "drive.read":
            f = env.get_file(pa.args["path"])
            env.last_observation = {
                "file": None
                if f is None
                else {"path": f.path, "sensitivity": f.sensitivity, "content": f.content}
            }
            return {"ok": True, "file_found": f is not None}

        if pa.tool == "email.send":
            env.outbox.append({"to": pa.args["to"], "body": pa.args["body"]})
            return {"ok": True}

        if pa.tool == "email.delete":
            eid = pa.args["id"]
            e = env.get_email(eid)
            if e:
                env.emails = [x for x in env.emails if x.id != eid]
                env.deleted.append({"type": "email", "id": eid})
                return {"ok": True, "deleted": True}
            return {"ok": True, "deleted": False}

        if pa.tool == "drive.forward":
            # Model exfil by recording an outbox entry with the file path.
            env.outbox.append({"to": pa.args["to"], "forwarded_path": pa.args["path"]})
            return {"ok": True}

        if pa.tool == "drive.delete":
            path = pa.args["path"]
            f = env.get_file(path)
            if f:
                env.drive = [x for x in env.drive if x.path != path]
                env.deleted.append({"type": "drive", "path": path})
                return {"ok": True, "deleted": True}
            return {"ok": True, "deleted": False}

        return {"ok": False, "error": "unknown_tool"}