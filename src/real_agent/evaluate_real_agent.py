from __future__ import annotations

import json
from pathlib import Path

from src.real_agent.cases_loader import list_case_names
from src.real_agent.config import REAL_AGENT_CONFIGS
from src.real_agent.logger import write_run_log, write_trace
from src.real_agent.qwen_agent_runner import load_model, run_case


def main():
    case_names = list_case_names()
    tokenizer, model = load_model()

    for case_name in case_names:
        for config_name, cfg in REAL_AGENT_CONFIGS.items():
            result = run_case(
                case_name=case_name,
                config_name=config_name,
                tokenizer=tokenizer,
                model=model,
                permission_mode=cfg["permission_mode"],
                policy_mode=cfg["policy_mode"],
            )

            log_obj = {
                "case_name": result.case_name,
                "config_name": result.config_name,
                "model_name": result.model_name,
                "final_answer": result.final_answer,
                "steps": result.steps,
            }
            trace_obj = {
                "case_name": result.case_name,
                "config_name": result.config_name,
                "trace": result.trace,
            }

            log_path = write_run_log(case_name, config_name, log_obj)
            trace_path = write_trace(case_name, config_name, trace_obj)

            print(f"Wrote log: {log_path}")
            print(f"Wrote trace: {trace_path}")
            print("FINAL ANSWER:", result.final_answer)
            print("TRACE LENGTH:", len(result.trace))
            print("=" * 80)


if __name__ == "__main__":
    main()
