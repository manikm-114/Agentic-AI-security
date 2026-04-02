from __future__ import annotations

REAL_AGENT_CONFIGS = {
    "broad_permissive": {
        "permission_mode": "broad",
        "policy_mode": "permissive",
    },
    "broad_strict": {
        "permission_mode": "broad",
        "policy_mode": "strict",
    },
    "least_strict": {
        "permission_mode": "least",
        "policy_mode": "strict",
    },
}

EXTERNAL_DOMAINS = ["external.test"]

LOCAL_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

MAX_NEW_TOKENS = 256
MAX_STEPS = 7
TEMPERATURE = 0.0


def is_external_recipient(recipient: str) -> bool:
    r = recipient.lower().strip()
    return any(r.endswith("@" + d) or r.endswith(d) for d in EXTERNAL_DOMAINS)

INTERNAL_DOMAINS = ["hospital.test"]

def is_internal_recipient(recipient: str) -> bool:
    r = recipient.lower().strip()
    return any(r.endswith("@" + d) or r.endswith(d) for d in INTERNAL_DOMAINS)
