#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime_skill_audit.config import load_config  # noqa: E402
from runtime_skill_audit.llm import OllamaCloudClient  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test the LLM endpoint configured for Runtime Skill Audit.")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "default.yaml"), help="Path to the RSA config YAML")
    parser.add_argument("--prompt", default="Reply with exactly: RSA LLM endpoint OK", help="Prompt used for the endpoint test")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    client = OllamaCloudClient(config.llm)
    response = client.complete(prompt=args.prompt, temperature=0.0)
    print(response)


if __name__ == "__main__":
    main()
