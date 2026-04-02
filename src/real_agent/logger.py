from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def logs_root() -> Path:
    p = repo_root() / "outputs" / "real_agent" / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def traces_root() -> Path:
    p = repo_root() / "outputs" / "real_agent" / "traces"
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def timestamp_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


def write_run_log(case_name: str, config_name: str, log_obj: dict[str, Any]) -> Path:
    path = logs_root() / f"{case_name}__{config_name}.json"
    write_json(path, log_obj)
    return path


def write_trace(case_name: str, config_name: str, trace_obj: dict[str, Any]) -> Path:
    path = traces_root() / f"{case_name}__{config_name}.json"
    write_json(path, trace_obj)
    return path


if __name__ == "__main__":
    sample_log = {"status": "ok", "ts": timestamp_utc()}
    sample_trace = {"trace": []}
    print(write_run_log("sample_case", "sample_config", sample_log))
    print(write_trace("sample_case", "sample_config", sample_trace))
