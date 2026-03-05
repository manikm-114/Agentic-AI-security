from __future__ import annotations

from pathlib import Path
import csv
from typing import Dict, List, Any

import matplotlib.pyplot as plt


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


def to_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


PERM_ORDER = ["work_only", "least_privilege", "work_plus_personal_read", "full", "all_read_all_forward"]


def order_perms(perms: List[str]) -> List[str]:
    known = [p for p in PERM_ORDER if p in perms]
    extras = sorted([p for p in perms if p not in set(PERM_ORDER)])
    return known + extras


def aggregate_by_permission(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    agg: Dict[str, Dict[str, float]] = {}
    for r in rows:
        p = r.get("permission_profile", "UNKNOWN")
        if p not in agg:
            agg[p] = {
                "sensitive_forwarded": 0.0,
                "sensitive_reads": 0.0,
                "false_deletes": 0.0,
                "blocked_by_permission": 0.0,
                "blocked_by_policy": 0.0,
                "attempted_high_risk": 0.0,
            }

        agg[p]["sensitive_forwarded"] += to_int(r.get("sensitive_forwarded"))
        agg[p]["sensitive_reads"] += to_int(r.get("sensitive_reads"))
        agg[p]["false_deletes"] += to_int(r.get("false_deletes"))
        agg[p]["blocked_by_permission"] += to_int(r.get("blocked_by_permission"))
        agg[p]["blocked_by_policy"] += to_int(r.get("blocked_by_policy"))
        agg[p]["attempted_high_risk"] += to_int(r.get("attempted_high_risk"))
    return agg


def fig1_permission_harm(agg: Dict[str, Dict[str, float]], out_path: Path) -> None:
    perms = order_perms(list(agg.keys()))
    x = list(range(len(perms)))

    y_forward = [agg[p]["sensitive_forwarded"] for p in perms]
    y_reads = [agg[p]["sensitive_reads"] for p in perms]
    y_delete = [agg[p]["false_deletes"] for p in perms]

    plt.figure()
    plt.plot(x, y_forward, marker="o", label="Sensitive forwarded")
    plt.plot(x, y_reads, marker="o", label="Sensitive reads")
    plt.plot(x, y_delete, marker="o", label="False deletes")

    plt.xticks(x, perms, rotation=30, ha="right")
    plt.title("Blast Radius vs Permission Scope (Permissive Policy)")
    plt.xlabel("Permission profile (ordered by scope)")
    plt.ylabel("Harm count across attack scenarios (sum)")
    plt.legend()
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()


def fig2_defended_blocks(agg: Dict[str, Dict[str, float]], out_path: Path) -> None:
    """Single-panel (camera-ready): why actions are blocked under strict policy."""
    perms = order_perms(list(agg.keys()))
    x = list(range(len(perms)))

    blocked_perm = [agg[p]["blocked_by_permission"] for p in perms]
    blocked_policy = [agg[p]["blocked_by_policy"] for p in perms]
    attempted = [agg[p]["attempted_high_risk"] for p in perms]

    fig, ax = plt.subplots(figsize=(9.2, 5.4))

    # Stacked bars: block source
    ax.bar(x, blocked_perm, label="Blocked by permissions")
    ax.bar(x, blocked_policy, bottom=blocked_perm, label="Blocked by policy")

    # Line: attempted actions
    ax.plot(x, attempted, marker="o", label="Attempted high-risk actions")

    ax.set_title("Defended Sweep (Strict Policy): Why Actions Are Blocked", pad=10)
    ax.set_xlabel("Permission profile (ordered by scope)")
    ax.set_ylabel("Count across attack scenarios (sum)")
    ax.set_xticks(x)
    ax.set_xticklabels(perms, rotation=25, ha="right")
    ax.grid(True, axis="y", alpha=0.25)

    # Legend outside (no overlap)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=True)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig3_scenario_breakdown(baseline_rows: List[Dict[str, Any]], defended_rows: List[Dict[str, Any]], out_path: Path) -> None:
    scenarios = ["s2_indirect_injection", "s3_overreach", "s4_cascade", "s5_clean_inbox"]
    harm_metrics = [
        ("sensitive_forwarded", "Sensitive forwarded"),
        ("sensitive_reads", "Sensitive reads"),
        ("false_deletes", "False deletes"),
    ]

    b = {r["scenario"]: r for r in baseline_rows}
    d = {r["scenario"]: r for r in defended_rows}

    x = list(range(len(scenarios)))
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.8), sharey=False)

    # ---- Baseline: stacked harms
    ax = axes[0]
    bottom = [0] * len(scenarios)
    for key, label in harm_metrics:
        vals = [to_int(b[s].get(key)) for s in scenarios]
        ax.bar(x, vals, bottom=bottom, label=label)
        bottom = [bottom[i] + vals[i] for i in range(len(vals))]
    ax.set_title("Baseline (Permissive)")
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=20, ha="right")
    ax.set_xlabel("Attack scenario")
    ax.set_ylabel("Harm count (stacked)")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="upper left", frameon=True, fontsize=8)

    # ---- Defended: show blocked attempts (NOT harm)
    ax = axes[1]
    blocked_perm = [to_int(d[s].get("blocked_by_permission")) for s in scenarios]
    blocked_policy = [to_int(d[s].get("blocked_by_policy")) for s in scenarios]
    attempted = [to_int(d[s].get("attempted_high_risk")) for s in scenarios]

    ax.bar(x, blocked_perm, label="Blocked by permissions")
    ax.bar(x, blocked_policy, bottom=blocked_perm, label="Blocked by policy")
    ax.plot(x, attempted, marker="o", label="Attempted high-risk")

    ax.set_title("Defended (Strict + Least)")
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=20, ha="right")
    ax.set_xlabel("Attack scenario")
    ax.set_ylabel("Blocked / attempted (count)")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="upper left", frameon=True, fontsize=8)

    fig.suptitle("Scenario Breakdown: Harm (Baseline) vs Blocking (Defended)")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig4_integrity(rows_a: List[Dict[str, Any]], rows_b: List[Dict[str, Any]], out_path: Path) -> None:
    """
    Camera-ready integrity figure.
    Left: single detection bar (100%).
    Right: per-scenario localization (first failing block index).
    """
    scenarios = ["s2_indirect_injection", "s3_overreach", "s4_cascade", "s5_clean_inbox"]

    def filt(rows):
        return {r.get("scenario"): r for r in rows if r.get("scenario") in scenarios}

    A = filt(rows_a)  # policy-only
    B = filt(rows_b)  # combined

    # Detection rate across scenarios
    det_vals = [to_int(A[s].get("tamper_detected", 0)) for s in scenarios if s in A]
    det_rate = sum(det_vals) / max(1, len(det_vals))

    # Per-scenario first-failure index
    failA = [to_int(A.get(s, {}).get("tampered_first_fail_idx")) for s in scenarios]
    failB = [to_int(B.get(s, {}).get("tampered_first_fail_idx")) for s in scenarios]

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4))

    # --- Left: single detection bar
    axes[0].bar([0], [det_rate])
    axes[0].set_xticks([0])
    axes[0].set_xticklabels(["All scenarios"], rotation=0)
    axes[0].set_ylim(0.0, 1.10)
    axes[0].set_title("Tamper detection rate")
    axes[0].set_ylabel("Rate")
    axes[0].grid(True, axis="y", alpha=0.25)

    axes[0].text(
        0, det_rate + 0.01,
        f"{det_rate*100:.0f}%",
        ha="center", va="bottom", fontsize=12
    )

    # --- Right: localization per scenario
    x = list(range(len(scenarios)))
    w = 0.36
    axes[1].bar([i - w/2 for i in x], failA, width=w, label="Policy-only")
    axes[1].bar([i + w/2 for i in x], failB, width=w, label="Combined")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(scenarios, rotation=20, ha="right")
    axes[1].set_title("Tamper localization (first failing block)")
    axes[1].set_ylabel("Block index")
    axes[1].grid(True, axis="y", alpha=0.25)
    axes[1].legend(frameon=True, fontsize=9, loc="upper left")

    fig.suptitle("Log Integrity: Detection and Localization", y=1.02)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")  # <-- camera-ready
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    tables = root / "outputs" / "tables"
    figs = root / "outputs" / "figures"
    figs.mkdir(parents=True, exist_ok=True)

    # Sweeps
    sweep_baseline = tables / "sweep_baseline_full_noaudit.csv"
    sweep_defended = tables / "sweep_gated_least_audit_verify.csv"

    if sweep_baseline.exists():
        rows = read_csv(sweep_baseline)
        agg = aggregate_by_permission(rows)
        fig1_permission_harm(agg, figs / "fig1_blast_radius_baseline.png")
        print(f"Wrote: {figs / 'fig1_blast_radius_baseline.png'}")

    if sweep_defended.exists():
        rows = read_csv(sweep_defended)
        agg = aggregate_by_permission(rows)
        fig2_defended_blocks(agg, figs / "fig2_defended_blocks.png")
        print(f"Wrote: {figs / 'fig2_defended_blocks.png'}")

    # Scenario breakdown
    baseline_main = tables / "baseline_full_noaudit.csv"
    defended_main = tables / "gated_least_audit_verify.csv"
    if baseline_main.exists() and defended_main.exists():
        b = read_csv(baseline_main)
        d = read_csv(defended_main)
        fig3_scenario_breakdown(b, d, figs / "fig3_scenario_breakdown.png")
        print(f"Wrote: {figs / 'fig3_scenario_breakdown.png'}")

    # Integrity
    policy_only = tables / "policy_only_full.csv"
    combined = tables / "gated_least_audit_verify.csv"
    if policy_only.exists() and combined.exists():
        a = read_csv(policy_only)
        b = read_csv(combined)
        fig4_integrity(a, b, figs / "fig4_integrity.png")
        print(f"Wrote: {figs / 'fig4_integrity.png'}")
    else:
        if combined.exists():
            b = read_csv(combined)
            fig4_integrity(b, b, "Defended", "Defended", figs / "fig4_integrity.png")
            print(f"Wrote: {figs / 'fig4_integrity.png'} (defended-only)")

    print("Done.")


if __name__ == "__main__":
    main()