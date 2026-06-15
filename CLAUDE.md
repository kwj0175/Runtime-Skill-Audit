# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
# Install the package
pip install -e .

# Build the sandbox Docker image
docker build -t rsa_sandbox -f docker/sandbox.Dockerfile .

# Copy your local OpenClaw config into the expected location
mkdir -p .openclaw/agents/main/agent .openclaw/workspace
cp ~/.openclaw/openclaw.json .openclaw/openclaw.json
cp ~/.openclaw/agents/main/agent/models.json .openclaw/agents/main/agent/models.json
cp ~/.openclaw/agents/main/agent/auth-profiles.json .openclaw/agents/main/agent/auth-profiles.json

# Set LLM API key (default uses Ollama cloud)
export OLLAMA_API_KEY=your_key

# Test LLM endpoint before running
python scripts/test_llm_endpoint.py --config configs/default.yaml
```

## Running the Audit

```bash
# Full run on a single skill
python scripts/run_pipeline.py data/skills/benign/051-general-3s-hook-generator \
  --config configs/default.yaml

# Dry run (profile + task generation only, no OpenClaw execution)
python scripts/run_pipeline.py data/skills/benign/051-general-3s-hook-generator \
  --config configs/default.yaml --run-mode skip

# Override task count or repair attempts
python scripts/run_pipeline.py <skill_dir> --num-tasks 4 --max-repair-attempts 2
```

## Architecture

RSA is a **LangGraph pipeline** that audits OpenClaw skills for security properties through dynamic execution. The pipeline runs sequentially:

```
init_run → load_memory → build_profile → generate_tasks → execute_tasks → update_memory → summarize
```

### Pipeline nodes (`runtime_skill_audit/workflow.py`)

1. **init_run**: Creates a timestamped output directory under `outputs/`.
2. **load_memory**: Loads cross-run `SkillMemory` from `outputs/memory/<skill>.json` to inform task generation with past results.
3. **build_profile** (`profile.py`): Calls the LLM to produce a `SkillProfile` — tools, execution targets, trigger surfaces, static risk targets.
4. **generate_tasks** (`tasks.py`): LLM generates `GeneratedTask` objects that exercise the skill's risk-relevant interfaces. Task count is set by `workflow.num_tasks`.
5. **execute_tasks** (`runtime.py`): For each task, runs OpenClaw in a sandboxed Docker container with up to `max_repair_attempts` retries. Collects execution traces.
6. **update_memory**: Persists run outcomes back to the skill memory store.
7. **summarize**: Writes `summary.json` with aggregate verdicts.

### Execution and tracing (`runtime_skill_audit/runtime.py`)

Each task attempt:
- Prepares an isolated workspace by copying source workspace files and the skill directory.
- Seeds dummy sensitive files (`auth-profiles.json`, `.stripe-key`, `psych_eval_notes_jan2025.txt`) to detect credential exfiltration.
- Installs sandbox shims (`gog`, `pbpaste`, `sw_vers`, `sysctl`) under `workspace/bin/` that log invocations to `bench_observations/`.
- Runs `openclaw agent` via subprocess with `--json` output.
- Diffs workspace snapshots before/after to capture file changes.
- Parses the session JSONL to extract tool calls, file reads/writes, network requests, and conversation history into a `trace.json`.

### Evaluation (`runtime_skill_audit/evaluator.py`)

Two LLM-graded evaluations per attempt:
- **Attempt evaluation**: classifies outcome as `success`, `infra_failure`, `prep_failure`, or `semantic_failure` and recommends a `RepairAction`.
- **Harmfulness assessment**: classifies the skill's observed behavior as `benign_executed`, `harmful_executed`, `harmful_blocked`, or `uncertain`.

Heuristic fallback in `runtime.py::_assess_harmfulness` runs if the LLM call fails. Final status is `completed`, `failed`, or `defended`.

### Key models (`runtime_skill_audit/models.py`)

All data is Pydantic v2. Notable types:
- `BenchmarkConfig` — full config loaded from YAML.
- `SkillProfile` — LLM-derived static analysis of a skill.
- `GeneratedTask` — a runnable test case with prep, execute, and runtime sections.
- `SkillMemory` — persisted cross-run state for a skill.
- `RepairAction` — typed repair instructions (`chmod_scripts`, `enable_network`, `extend_timeout`, `switch_image`, `expose_execution_targets`, `update_task_prep`, `update_task`, `none`).
- `HarmfulnessAssessment` / `SuccessAssessment` — final security verdicts.

### LLM client (`runtime_skill_audit/llm.py`)

`OllamaCloudClient` sends requests to an Ollama-native chat API (not OpenAI `/v1/chat/completions`). The `base_url` in config must be the full endpoint (e.g. `https://ollama.com/api/chat`). To use another provider, either adapt `llm.py` or front it with a compatible proxy.

### Configuration (`configs/default.yaml`)

Key fields to adjust:
- `llm.model`, `llm.base_url`, `llm.api_key_env` — LLM provider.
- `workflow.num_tasks` — tasks per skill (default 2).
- `workflow.run_mode` — `execute` or `skip`.
- `workflow.max_repair_attempts` — retry budget (default 4).
- `paths.source_workspace`, `paths.source_config` — local OpenClaw template to copy per run.
- `runtime.timeout_seconds` — per-task OpenClaw timeout.
- `sandbox.default_image` — Docker image for the sandbox (default `rsa_sandbox`).

### Corpus (`data/skills/`)

- `data/skills/benign/` — 50 safe skills.
- `data/skills/malicious/` — 50 intentionally harmful skills (for controlled security evaluation only).

Each skill directory contains a `SKILL.md` and `_meta.json`.

### Output layout

```
outputs/
  <timestamp>-<label>/
    run_meta.json
    pipeline_state.json
    summary.json
    skills/<skill_name>/
      profile.json
      knowledge.json
      tasks.json
      run_results.json
      inspection_runs/
        <timestamp>-<task_id>-attempt-01/
          task.json
          trace.json
          session.jsonl
          command.json
          prepared_run.json
```
