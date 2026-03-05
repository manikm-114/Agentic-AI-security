from __future__ import annotations

from pathlib import Path
from src.runner import run_suite


def main() -> None:
    root = Path(__file__).resolve().parents[1]

    run_cfgs = [
        root / "configs/runs/baseline.json",
        root / "configs/runs/perm_only_least.json",
        root / "configs/runs/policy_only_full.json",
        root / "configs/runs/gated_audit.json",
    ]

    for cfg in run_cfgs:
        run_suite(root, cfg)


if __name__ == "__main__":
    main()