#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime_skill_audit.workflow import run_pipeline  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Runtime Skill Audit for one agent skill.")
    parser.add_argument("skill", help="Path to the OpenClaw skill directory")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "default.yaml"), help="Path to the RSA config YAML")
    parser.add_argument("--label", help="Optional run label override")
    parser.add_argument("--num-tasks", type=int, help="Optional task count override")
    parser.add_argument("--run-mode", choices=["skip", "execute"], help="Optional run mode override")
    parser.add_argument("--max-repair-attempts", type=int, help="Optional repair attempt override")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_pipeline(
        args.skill,
        args.config,
        label=args.label,
        num_tasks=args.num_tasks,
        run_mode=args.run_mode,
        max_repair_attempts=args.max_repair_attempts,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
