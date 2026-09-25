# Minimal Coding Agent

A deliberately small Coding Agent for learning the core agent loop step by step.

Current version: **v0.2**

## How it works

```text
User Task
  -> CodingAgent
  -> LLM
  -> Tool Call
  -> Tool Execution
  -> Tool Result
  -> LLM
  -> ...
  -> Final Answer
```

The model currently has four tools:

- `list_files`
- `read_file`
- `write_file`
- `run_command`

`Workspace` owns the filesystem boundary. `CodingAgent` owns the model/tool loop.
`AgentConfig` owns model and API connection configuration.

## Install

Python 3.10+ is required.

```bash
python -m venv .venv
pip install -e ".[dev]"
```

## Model and API configuration

v0.2 supports a custom API key, base URL, model, and maximum agent steps.

Configuration precedence is:

```text
CLI argument
  -> environment variable
  -> built-in default
```

Supported environment variables:

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
CODING_AGENT_MAX_STEPS
```

PowerShell example:

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_MODEL="gpt-6-sol"

coding-agent "Create a hello world Python program and run it"
```

Custom OpenAI-compatible endpoint:

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_BASE_URL="https://example.com/v1"
$env:OPENAI_MODEL="your-model"

coding-agent "Inspect this project and summarize its structure"
```

The endpoint must support the Responses API and the function-calling behavior used by this agent.
An API that only imitates Chat Completions is not sufficient.

CLI overrides are also available:

```bash
coding-agent "Add a /health endpoint" \
  --workspace ./my-project \
  --api-key your-key \
  --base-url https://example.com/v1 \
  --model your-model \
  --max-steps 12
```

Prefer `OPENAI_API_KEY` over `--api-key`, because command-line arguments can be stored in shell history or exposed to process inspection.

The built-in defaults are:

```text
model: gpt-6-sol
max_steps: 20
```

The workspace directory must already exist.

## Tests

```bash
pytest
```

Unit tests do not call a real LLM API. The Agent Loop test uses a fake client.
GitHub Actions runs `pytest -q` on pushes to `main` and on pull requests.

## Safety limits

This is **not a sandbox**.

- File paths are confined to the configured workspace.
- Absolute paths and `../` path escapes are rejected.
- Commands run without a shell and executable names are allow-listed.
- Git is limited to `status`, `diff`, `log`, and `show`.
- Commands time out and stdout/stderr are truncated.
- Allow-listed interpreters such as Python can still execute arbitrary code with the current user's OS permissions.
- API keys are not stored by `AgentConfig` outside process memory and are hidden from its `repr`.

Use an isolated test workspace for untrusted tasks.

## Roadmap

- v0.1: minimal Agent Loop and coding tools
- v0.2: model/API configuration
- v0.3: AgentState and ContextManager
- v0.4: context compression
- v0.5: SubAgent runtime
- v0.6: deterministic DAG scheduler
- v0.7: DAG + SubAgent execution
- v0.8: Root Agent plans and validates dynamic DAGs

## Intentionally not implemented yet

v0.2 does not yet include multi-agent orchestration, context compression, memory, RAG, vector databases, DAG execution, MCP, a web UI, Docker sandboxing, or automatic Git commit/push.
