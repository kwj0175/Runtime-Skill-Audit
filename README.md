# Runtime Skill Audit

Runtime Skill Audit (RSA) is a dynamic analysis method for auditing agent skills through targeted runtime probing. RSA profiles risk-relevant skill interfaces, generates task scenarios that exercise those interfaces, executes the skill in a sandboxed agent environment, and assigns security labels from runtime traces.

This repository contains the cleaned implementation used for the paper experiments, together with the 100-skill evaluation corpus.

## Requirements

- Python 3.10 or newer
- Docker, used by the OpenClaw sandbox runtime
- Openclaw
- An LLM endpoint for profiling, task generation, repair, and trace judgment


## Environment Setup

### Python environment
Install the Python package in editable mode:

```bash
pip install -e .
```

### Sandbox
Build the sandbox image used by the default configuration:

```bash
docker build -t rsa_sandbox -f docker/sandbox.Dockerfile .
```

The sandbox uses a normal Linux/Python base image, but replaces a small set of high-risk or network-facing commands such as `curl`, `wget`, `ping`, `dig`, `nc`, and `git` with lightweight wrappers. This keeps malicious-skill evaluation more deterministic and safer. Basic shell behavior and ordinary commands such as `cd`, `ls`, `cat`, and path operations remain provided by the base system.

### OpenClaw
Install [OpenClaw](https://github.com/openclaw/openclaw) following official instructions, then check that the CLI is available:

```bash
openclaw --version
```

### LLM configuration

RSA uses the LLM for skill profiling, task generation, repair decisions, and trace-grounded judgment. In `configs/default.yaml`, `llm.base_url` is the full chat-completion endpoint that RSA will `POST` to, not only a host name.

#### Quick Start with Ollama API

Create an Ollama API key from the official [Ollama API keys page](https://ollama.com/settings/keys), then export it locally.

```bash
export OLLAMA_API_KEY=your_ollama_api_key
```

The default configuration uses the Ollama cloud chat endpoint:

```yaml
llm:
  model: gpt-oss:120b
  base_url: https://ollama.com/api/chat
  api_key_env: OLLAMA_API_KEY
  temperature: 0.1
  timeout: 120
  max_retries: 3
```

Test the configured endpoint before running the full audit:

```bash
python scripts/test_llm_endpoint.py --config configs/default.yaml
```

#### Configure a Custom LLM

To use another endpoint, edit the `llm` block in `configs/default.yaml`. The `api_key_env` field should be the name of an environment variable, not the API key itself:

```yaml
llm:
  model: your-model-name
  base_url: https://your-provider.example.com/api/chat
  api_key_env: MY_LLM_API_KEY
```

Before running RSA, set that environment variable in your shell:

```bash
export MY_LLM_API_KEY=your_real_api_key
python scripts/test_llm_endpoint.py --config configs/default.yaml
```

The default client expects the Ollama native chat API shape: request fields include `model`, `messages`, `stream`, and `options`, and the response should contain `message.content`. If your provider exposes a different protocol, such as OpenAI `/v1/chat/completions`, use a compatible proxy or adapt `runtime_skill_audit/llm.py`.



## OpenClaw Configuration

RSA creates a fresh temporary OpenClaw state for each run, but it needs a local OpenClaw configuration as the template. By default, `configs/default.yaml` expects the template under `.openclaw/` in this repository:

```yaml
paths:
  source_workspace: .openclaw/workspace
  source_config: .openclaw/openclaw.json
```

Export or copy your local OpenClaw configuration into that location:

```bash
mkdir -p .openclaw/agents/main/agent .openclaw/workspace

cp ~/.openclaw/openclaw.json .openclaw/openclaw.json
cp ~/.openclaw/agents/main/agent/models.json .openclaw/agents/main/agent/models.json
cp ~/.openclaw/agents/main/agent/auth-profiles.json .openclaw/agents/main/agent/auth-profiles.json
```

These files may contain local account or model configuration. 
If your OpenClaw files live elsewhere, either copy them into `.openclaw/` or update `paths.source_config` and `paths.source_workspace` in `configs/default.yaml`.

## Start auditing

Run RSA on a single skill directory:

```bash
python scripts/run_pipeline.py data/skills/benign/051-general-3s-hook-generator \
  --config configs/default.yaml
```

For a dry run that profiles and generates tasks without executing OpenClaw, use:

```bash
python scripts/run_pipeline.py data/skills/benign/051-general-3s-hook-generator \
  --config configs/default.yaml \
  --run-mode skip
```

Runtime outputs are written to the configured `outputs/` directory.

## Data

The included corpus contains:

- `data/skills/benign`: 50 benign skills.
- `data/skills/malicious`: 50 intentionally malicious skills for controlled security evaluation.

The malicious skills are for research and defense evaluation only. Run them only in isolated sandbox environments.

## Safety and Privacy

The repository has been cleaned to remove local run outputs, caches, personal workspace paths, and credentials. The code reads API credentials only from user-provided environment variables or from the local `.openclaw/` configuration you provide. The included dataset uses synthetic or curated skill artifacts and does not include real API keys or real user credentials.
