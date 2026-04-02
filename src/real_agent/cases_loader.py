from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RealValidationCase:
    case_dir: Path
    task: dict[str, Any]
    emails: list[dict[str, Any]]
    documents: list[dict[str, Any]]
    expected: dict[str, Any]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cases_root() -> Path:
    return repo_root() / "data" / "real_validation" / "cases"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_case(case_name: str) -> RealValidationCase:
    case_dir = cases_root() / case_name
    if not case_dir.exists():
        raise FileNotFoundError(f"Case directory not found: {case_dir}")

    task = load_json(case_dir / "task.json")
    emails = load_json(case_dir / "emails.json")
    documents = load_json(case_dir / "documents.json")
    expected = load_json(case_dir / "expected.json")

    return RealValidationCase(
        case_dir=case_dir,
        task=task,
        emails=emails,
        documents=documents,
        expected=expected,
    )


def list_case_names() -> list[str]:
    root = cases_root()
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def case_summary(case: RealValidationCase) -> dict[str, Any]:
    return {
        "case_id": case.task.get("case_id"),
        "scenario_id": case.task.get("scenario_id"),
        "goal": case.task.get("goal"),
        "email_count": len(case.emails),
        "document_count": len(case.documents),
        "outcome_axis": case.expected.get("outcome_axis"),
        "mechanism_axis": case.expected.get("mechanism_axis"),
        "structure_axis": case.expected.get("structure_axis"),
    }


if __name__ == "__main__":
    names = list_case_names()
    print("Found cases:", names)
    if names:
        c = load_case(names[0])
        print(case_summary(c))
