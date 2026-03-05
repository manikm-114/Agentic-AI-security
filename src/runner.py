from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.env.loaders import load_default_env, load_json, apply_attack_injection
from src.agent.planner import Planner
from src.agent.agent import ToolAgent
from src.defenses.permissions import PermissionProfile
from src.defenses.policy_gate import PolicyGate
from src.history.verifier import verify_history
from src.history.tamper import (
    tamper_one_field,
    verify_chain_dicts,
    integrity_delta_from_dicts,
    first_failure_index,
    write_json,
)
from src.eval.metrics import (
    MetricRow,
    compute_outbox_metrics,
    compute_overreach,
    compute_sensitive_reads,
    compute_false_deletes,
    compute_attempt_block_metrics,
)
from src.eval.tables import write_csv


def load_permission_profile(path: Path) -> PermissionProfile:
    cfg = load_json(path)
    return PermissionProfile(name=cfg["name"], rules=cfg["rules"])


def load_policy(path: Path) -> PolicyGate:
    cfg = load_json(path)
    return PolicyGate(mode=cfg.get("mode", "strict"))


def run_one(
    *,
    run_name: str,
    scenario_name: str,
    task_path: Path,
    attack_path: Optional[Path],
    permission_path: Path,
    policy_path: Path,
    use_audit: bool,
    use_verifier: bool,
    simulate_tamper: bool,
    out_root: Path,
) -> MetricRow:
    env0 = load_default_env()
    task = load_json(task_path)

    if attack_path is not None:
        attack = load_json(attack_path)
        apply_attack_injection(env0, attack)

    env_before = env0.clone()

    profile = load_permission_profile(permission_path)
    gate = load_policy(policy_path)

    agent = ToolAgent(planner=Planner())
    trace_records, log = agent.run(
        env=env0,
        task=task,
        profile=profile,
        gate=gate,
        use_audit=use_audit,
        step_limit=10,
    )

    trace: List[Dict[str, Any]] = []
    env_hashes: List[str] = []
    for r in trace_records:
        trace.append(
            {
                "step": r.step,
                "proposal": r.proposal,
                "decision": r.decision,
                "result": r.result,
                "env_hash": r.env_hash,
            }
        )
        env_hashes.append(r.env_hash)

    # Save trace
    trace_path = out_root / "outputs" / "traces" / f"{run_name}__{scenario_name}.json"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(json.dumps(trace, indent=2), encoding="utf-8")

    integrity_delta = 0.0
    tamper_detected = 0
    tampered_integrity_delta = 0.0
    tampered_first_fail_idx = -1

    if use_audit and log is not None:
        log_list = log.to_list()
        log_path = out_root / "outputs" / "logs" / f"{run_name}__{scenario_name}.json"
        write_json(log_path, log_list)

        if use_verifier:
            rep = verify_history(log, expected_env_hashes=env_hashes)
            integrity_delta = rep.integrity_delta

        if simulate_tamper:
            # IMPORTANT: scenario-dependent tamper target
            tampered = tamper_one_field(log_list, scenario_name=scenario_name)
            tampered_path = out_root / "outputs" / "logs" / f"{run_name}__{scenario_name}__TAMPERED.json"
            write_json(tampered_path, tampered)

            chain_ok = verify_chain_dicts(tampered)
            tamper_detected = 0 if chain_ok else 1
            tampered_integrity_delta = integrity_delta_from_dicts(tampered, expected_env_hashes=env_hashes)
            tampered_first_fail_idx = first_failure_index(tampered)

    outbox_m = compute_outbox_metrics(env_before, env0)
    overreach = compute_overreach(trace, goal_required_paths=["/work/report.txt"])
    sensitive_paths = [f.path for f in env_before.drive if f.sensitivity == "personal_sensitive"]
    sensitive_reads = compute_sensitive_reads(trace, sensitive_paths=sensitive_paths)
    false_deletes = compute_false_deletes(env0)

    attempt_m = compute_attempt_block_metrics(trace)

    return MetricRow(
        scenario=scenario_name,
        run_name=run_name,
        messages_sent=outbox_m["messages_sent"],
        forward_events=outbox_m["forward_events"],
        sensitive_forwarded=outbox_m["sensitive_forwarded"],
        overreach_ratio=overreach,
        sensitive_reads=sensitive_reads,
        false_deletes=false_deletes,
        attempted_high_risk=attempt_m["attempted_high_risk"],
        allowed_high_risk=attempt_m["allowed_high_risk"],
        blocked_by_permission=attempt_m["blocked_by_permission"],
        blocked_by_policy=attempt_m["blocked_by_policy"],
        integrity_delta=integrity_delta,
        tamper_detected=tamper_detected,
        tampered_integrity_delta=tampered_integrity_delta,
        tampered_first_fail_idx=tampered_first_fail_idx,
        steps=len(trace),
    )


def run_suite(out_root: Path, run_cfg_path: Path) -> None:
    cfg = load_json(run_cfg_path)

    run_name = cfg["run_name"]
    permission_path = (out_root / cfg["permission_profile"]).resolve()
    policy_path = (out_root / cfg["policy"]).resolve()
    use_audit = bool(cfg.get("use_audit", True))
    use_verifier = bool(cfg.get("use_verifier", True))
    simulate_tamper = bool(cfg.get("simulate_tamper", use_audit and use_verifier))

    scenarios = [
        {"scenario_name": "s1_normal_summarize", "task_path": out_root / "data/tasks/t1_summarize_report.json", "attack_path": None},
        {"scenario_name": "s2_indirect_injection", "task_path": out_root / "data/tasks/t2_process_latest_email.json", "attack_path": out_root / "data/attacks/a1_indirect_injection.json"},
        {"scenario_name": "s3_overreach", "task_path": out_root / "data/tasks/t3_overreach_read.json", "attack_path": out_root / "data/attacks/a2_overreach_prompt.json"},
        {"scenario_name": "s4_cascade", "task_path": out_root / "data/tasks/t4_cascade.json", "attack_path": out_root / "data/attacks/a3_cascade_delete.json"},
        {"scenario_name": "s5_clean_inbox", "task_path": out_root / "data/tasks/t5_clean_inbox.json", "attack_path": out_root / "data/attacks/a4_clean_inbox_misgeneralize.json"},
    ]

    rows: List[Dict[str, Any]] = []
    for s in scenarios:
        row = run_one(
            run_name=run_name,
            scenario_name=s["scenario_name"],
            task_path=s["task_path"],
            attack_path=s["attack_path"],
            permission_path=permission_path,
            policy_path=policy_path,
            use_audit=use_audit,
            use_verifier=use_verifier,
            simulate_tamper=simulate_tamper,
            out_root=out_root,
        )
        rows.append(row.to_dict())

    table_path = out_root / "outputs" / "tables" / f"{run_name}.csv"
    write_csv(table_path, rows)
    print(f"Wrote results: {table_path}")

    sweep_rows = run_permission_sweep(
        out_root=out_root,
        run_name=run_name,
        policy_path=policy_path,
        use_audit=use_audit,
        use_verifier=use_verifier,
        simulate_tamper=simulate_tamper,
    )
    sweep_path = out_root / "outputs" / "tables" / f"sweep_{run_name}.csv"
    write_csv(sweep_path, sweep_rows)
    print(f"Wrote sweep: {sweep_path}")


def run_permission_sweep(
    *,
    out_root: Path,
    run_name: str,
    policy_path: Path,
    use_audit: bool,
    use_verifier: bool,
    simulate_tamper: bool,
) -> List[Dict[str, Any]]:
    perm_dir = out_root / "configs/permission_scopes"
    perm_profiles = sorted([p for p in perm_dir.glob("*.json") if p.is_file()])

    attack_scenarios = [
        ("s2_indirect_injection", out_root / "data/tasks/t2_process_latest_email.json", out_root / "data/attacks/a1_indirect_injection.json"),
        ("s3_overreach", out_root / "data/tasks/t3_overreach_read.json", out_root / "data/attacks/a2_overreach_prompt.json"),
        ("s4_cascade", out_root / "data/tasks/t4_cascade.json", out_root / "data/attacks/a3_cascade_delete.json"),
        ("s5_clean_inbox", out_root / "data/tasks/t5_clean_inbox.json", out_root / "data/attacks/a4_clean_inbox_misgeneralize.json"),
    ]

    rows: List[Dict[str, Any]] = []
    for perm_path in perm_profiles:
        perm_name = perm_path.stem
        for scenario_name, task_path, attack_path in attack_scenarios:
            row = run_one(
                run_name=f"{run_name}__sweep_{perm_name}",
                scenario_name=scenario_name,
                task_path=task_path,
                attack_path=attack_path,
                permission_path=perm_path.resolve(),
                policy_path=policy_path.resolve(),
                use_audit=use_audit,
                use_verifier=use_verifier,
                simulate_tamper=simulate_tamper,
                out_root=out_root,
            ).to_dict()
            row["permission_profile"] = perm_name
            rows.append(row)

    return rows