# Runtime Skill Audit

Runtime Skill Audit (RSA) is a dynamic analysis method for auditing agent skills through targeted runtime probing. RSA profiles risk-relevant skill interfaces, generates task scenarios that exercise those interfaces, executes the skill in a sandboxed agent environment, and assigns security labels from runtime traces.

This repository contains the cleaned implementation used for the paper experiments, together with the 100-skill evaluation corpus.

## Repository Layout

- `runtime_skill_audit/`: core RSA Python package.
- `scripts/run_pipeline.py`: command-line entry point for auditing one skill.
- `configs/default.yaml`: default configuration template.
- `knowledge_base.json`: reusable security knowledge used for profiling, task generation, and trace judgment.
- `docker/`: sandbox image definition and helper command shims.
- `data/skill_corpus/balanced_100/`: 50 benign and 50 malicious skills used in the paper evaluation.

## Installation

```bash
pip install -e .
```

RSA expects an OpenClaw-compatible runtime and an LLM endpoint configured by `configs/default.yaml`. API keys are not stored in this repository; configure credentials through environment variables.

## Basic Usage

Run RSA on a single skill directory:

```bash
python scripts/run_pipeline.py data/skill_corpus/balanced_100/benign/051-general-3s-hook-generator \
  --config configs/default.yaml
```

Build the sandbox image if needed:

```bash
docker build -t rsa_sandbox -f docker/sandbox.Dockerfile .
```

Runtime outputs are written to the configured `outputs/` directory, which is ignored by Git.

## Data

The included corpus contains:

- `data/skill_corpus/balanced_100/benign`: 50 benign skills.
- `data/skill_corpus/balanced_100/malicious`: 50 intentionally malicious skills for controlled security evaluation.

The malicious skills are for research and defense evaluation only. Run them only in isolated sandbox environments.

## Safety and Privacy

The repository has been cleaned to remove local run outputs, caches, personal workspace paths, and credentials. The code reads API credentials only from user-provided environment variables. The included dataset uses synthetic or curated skill artifacts and does not include real API keys or real user credentials.
