from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
import hashlib


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _block_hash(block: Dict[str, Any]) -> str:
    payload = dict(block)
    payload["hash"] = ""
    return _sha256_hex(json.dumps(payload, sort_keys=True))


def first_failure_index(blocks: List[Dict[str, Any]]) -> int:
    """Return the first block index i that fails verification; -1 if all ok."""
    if not blocks:
        return 0

    # genesis
    if _block_hash(blocks[0]) != blocks[0].get("hash", ""):
        return 0

    for i in range(1, len(blocks)):
        prev = blocks[i - 1]
        cur = blocks[i]
        if cur.get("prev_hash") != prev.get("hash"):
            return i
        if _block_hash(cur) != cur.get("hash", ""):
            return i
    return -1


def verify_chain_dicts(blocks: List[Dict[str, Any]]) -> bool:
    return first_failure_index(blocks) == -1


def integrity_delta_from_dicts(blocks: List[Dict[str, Any]], expected_env_hashes: List[str]) -> float:
    """If chain invalid -> 1.0. Else env_hash mismatch fraction."""
    if len(blocks) <= 1:
        return 0.0

    fail = first_failure_index(blocks)
    if fail != -1:
        return 1.0

    non_genesis = blocks[1:]
    denom = max(1, len(non_genesis))

    mismatched = 0
    for i, b in enumerate(non_genesis):
        if i >= len(expected_env_hashes):
            break
        if b.get("env_hash") != expected_env_hashes[i]:
            mismatched += 1
    return min(1.0, mismatched / denom)


def choose_tamper_index(blocks: List[Dict[str, Any]], scenario_name: str) -> int:
    """Choose a deterministic tamper index in [1, len(blocks)-1]."""
    if len(blocks) < 2:
        return 0
    # Use scenario hash to select index
    h = int(_sha256_hex(scenario_name), 16)
    # choose among non-genesis blocks
    return 1 + (h % (len(blocks) - 1))


def tamper_one_field(blocks: List[Dict[str, Any]], scenario_name: str) -> List[Dict[str, Any]]:
    """Flip one field in a deterministic block (scenario-dependent), without recomputing hashes."""
    if len(blocks) < 3:
        return list(blocks)

    tampered = json.loads(json.dumps(blocks))
    idx = choose_tamper_index(tampered, scenario_name=scenario_name)

    b = tampered[idx]
    # Change a meaningful but simple field
    b["tool"] = (b.get("tool", "") + "_TAMPERED")

    return tampered


def write_json(path, obj) -> None:
    from pathlib import Path
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")