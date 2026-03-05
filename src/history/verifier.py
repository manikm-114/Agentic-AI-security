from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .verilog import VeriLog

@dataclass
class IntegrityReport:
    chain_ok: bool
    missing_steps: int
    mismatched_env_hash: int
    integrity_delta: float  # fraction of suspect blocks (excluding genesis)
    notes: List[str]

def verify_history(log: VeriLog, expected_env_hashes: List[str]) -> IntegrityReport:
    """A simple verifier:
    - verifies hash chain
    - checks env_hash recorded per step matches the expected hash list
    expected_env_hashes should align with log blocks 1..N (post-genesis).
    """
    notes: List[str] = []
    chain_ok = log.verify_chain()
    if not chain_ok:
        notes.append("Hash chain verification failed (tampering or corruption).")

    blocks = log.blocks[1:]  # skip genesis
    missing_steps = 0
    mismatched = 0

    if len(expected_env_hashes) < len(blocks):
        missing_steps = len(blocks) - len(expected_env_hashes)
        notes.append("Expected env hash list shorter than log length (missing steps).")

    for i, b in enumerate(blocks):
        if i >= len(expected_env_hashes):
            break
        if b.env_hash != expected_env_hashes[i]:
            mismatched += 1

    suspect = (0 if chain_ok else len(blocks)) + missing_steps + mismatched
    denom = max(1, len(blocks))
    integrity_delta = min(1.0, suspect / denom)

    return IntegrityReport(
        chain_ok=chain_ok,
        missing_steps=missing_steps,
        mismatched_env_hash=mismatched,
        integrity_delta=integrity_delta,
        notes=notes
    )
