from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def traces_root() -> Path:
    return repo_root() / "outputs" / "real_agent" / "traces"


def tables_root() -> Path:
    p = repo_root() / "outputs" / "real_agent" / "tables"
    p.mkdir(parents=True, exist_ok=True)
    return p


def classify_trace(trace):
    forward_attempted = 0
    forward_allowed = 0
    forward_blocked_perm = 0
    forward_blocked_policy = 0
    delete_attempted = 0
    delete_allowed = 0
    delete_blocked_perm = 0
    delete_blocked_policy = 0

    for step in trace:
        action = step.get("action")
        allowed = step.get("allowed")
        blocked_by_permission = step.get("blocked_by_permission", False)
        blocked_by_policy = step.get("blocked_by_policy", False)

        if action == "forward_document":
            forward_attempted += 1
            if allowed:
                forward_allowed += 1
            elif blocked_by_permission:
                forward_blocked_perm += 1
            elif blocked_by_policy:
                forward_blocked_policy += 1

        if action in {"delete_email", "delete_document"}:
            delete_attempted += 1
            if allowed:
                delete_allowed += 1
            elif blocked_by_permission:
                delete_blocked_perm += 1
            elif blocked_by_policy:
                delete_blocked_policy += 1

    return {
        "forward_attempted": forward_attempted,
        "forward_allowed": forward_allowed,
        "forward_blocked_perm": forward_blocked_perm,
        "forward_blocked_policy": forward_blocked_policy,
        "delete_attempted": delete_attempted,
        "delete_allowed": delete_allowed,
        "delete_blocked_perm": delete_blocked_perm,
        "delete_blocked_policy": delete_blocked_policy,
    }


def main():
    rows = []
    for path in sorted(traces_root().glob("*.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        case_name = obj["case_name"]
        config_name = obj["config_name"]
        trace = obj["trace"]

        metrics = classify_trace(trace)

        rows.append({
            "case_name": case_name,
            "config_name": config_name,
            "trace_len": len(trace),
            **metrics,
        })

    out_path = tables_root() / "real_agent_summary.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            "case_name", "config_name", "trace_len",
            "forward_attempted", "forward_allowed", "forward_blocked_perm", "forward_blocked_policy",
            "delete_attempted", "delete_allowed", "delete_blocked_perm", "delete_blocked_policy",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote: {out_path}")
    print(f"Rows: {len(rows)}")


if __name__ == "__main__":
    main()
