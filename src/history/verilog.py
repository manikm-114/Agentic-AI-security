from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List
import time
import json

from .hashing import sha256_hex


SCHEMA_VERSION = "verilog_v1"


@dataclass
class LogBlock:
    idx: int
    ts: float
    schema_version: str
    action: str
    tool: str
    args: Dict[str, Any]
    result: Dict[str, Any]
    decision: Dict[str, Any]               # allow/deny + reasons
    permissions_snapshot: Dict[str, Any]
    env_hash: str
    prev_hash: str
    hash: str


class VeriLog:
    """Tamper-evident append-only log (hash chained)."""

    def __init__(self) -> None:
        genesis = LogBlock(
            idx=0,
            ts=time.time(),
            schema_version=SCHEMA_VERSION,
            action="GENESIS",
            tool="",
            args={},
            result={},
            decision={"allowed": True, "reason": "genesis"},
            permissions_snapshot={},
            env_hash="",
            prev_hash="0" * 64,
            hash="",
        )
        genesis.hash = self._compute_hash(genesis)
        self.blocks: List[LogBlock] = [genesis]

    def _compute_hash(self, b: LogBlock) -> str:
        payload = asdict(b).copy()
        payload["hash"] = ""  # exclude hash field from its own hash
        return sha256_hex(json.dumps(payload, sort_keys=True))

    def append(
        self,
        *,
        action: str,
        tool: str,
        args: Dict[str, Any],
        result: Dict[str, Any],
        decision: Dict[str, Any],
        permissions_snapshot: Dict[str, Any],
        env_hash: str,
    ) -> LogBlock:
        prev = self.blocks[-1]
        b = LogBlock(
            idx=len(self.blocks),
            ts=time.time(),
            schema_version=SCHEMA_VERSION,
            action=action,
            tool=tool,
            args=args,
            result=result,
            decision=decision,
            permissions_snapshot=permissions_snapshot,
            env_hash=env_hash,
            prev_hash=prev.hash,
            hash="",
        )
        b.hash = self._compute_hash(b)
        self.blocks.append(b)
        return b

    def verify_chain(self) -> bool:
        for i in range(1, len(self.blocks)):
            cur = self.blocks[i]
            prev = self.blocks[i - 1]
            if cur.prev_hash != prev.hash:
                return False
            if self._compute_hash(cur) != cur.hash:
                return False
        return True

    def to_list(self) -> List[Dict[str, Any]]:
        return [asdict(b) for b in self.blocks]