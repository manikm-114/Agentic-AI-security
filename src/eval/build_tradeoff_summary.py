from __future__ import annotations

from pathlib import Path
import csv
from typing import Dict, List, Any


PERM_ORDER = [
    "work_only",
    "least_privilege",
    "work_plus_personal_read",
    "full",
    "all_read_all_forward",
]


def read_csv(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


def to_int(x: Any) -> int:
    try:
        return int(float(x))
    except Exception:
        return 0


def aggregate(rows: List[Dict[str, Any]], policy_name: str) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}

    for r in rows:
        perm = r.get("permission_profile", "UNKNOWN")
        if perm not in grouped:
            grouped[perm] = {
                "permission_profile": perm,
                "policy_mode": policy_name,
                "sensitive_forwarded": 0,
                "sensitive_reads": 0,
                "false_deletes": 0,
                "total_harm": 0,
                "attempted_high_risk": 0,
                "allowed_high_risk": 0,
                "blocked_by_permission": 0,
                "blocked_by_policy": 0,
            }

        grouped[perm]["sensitive_forwarded"] += to_int(r.get("sensitive_forwarded"))
        grouped[perm]["sensitive_reads"] += to_int(r.get("sensitive_reads"))
        grouped[perm]["false_deletes"] += to_int(r.get("false_deletes"))
        grouped[perm]["attempted_high_risk"] += to_int(r.get("attempted_high_risk"))
        grouped[perm]["allowed_high_risk"] += to_int(r.get("allowed_high_risk"))
        grouped[perm]["blocked_by_permission"] += to_int(r.get("blocked_by_permission"))
        grouped[perm]["blocked_by_policy"] += to_int(r.get("blocked_by_policy"))

    rows_out = []
    for perm in PERM_ORDER:
        if perm in grouped:
            row = grouped[perm]
            row["total_harm"] = (
                row["sensitive_forwarded"]
                + row["sensitive_reads"]
                + row["false_deletes"]
            )
            rows_out.append(row)

    return rows_out


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    tables = root / "outputs" / "tables"

    permissive_path = tables / "sweep_baseline_full_noaudit.csv"
    strict_path = tables / "sweep_gated_least_audit_verify.csv"

    permissive_rows = read_csv(permissive_path)
    strict_rows = read_csv(strict_path)

    summary_rows = []
    summary_rows.extend(aggregate(permissive_rows, "permissive"))
    summary_rows.extend(aggregate(strict_rows, "strict"))

    out_path = tables / "tradeoff_summary.csv"
    write_csv(out_path, summary_rows)

    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()