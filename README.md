# Minimal Coding Agent

A deliberately small Coding Agent for learning the core agent loop step by step.

Current version: **v0.3**

## Architecture

```text
User Task
   ↓
CodingAgent
   ↓
AgentState
   ↕
ContextManager
   ↓
LLM
   ↓
Tool Call
   ↓
CodingTools
   ↓
Tool Result
   ↓
ContextManager
   ↓
LLM
   ↓
...
   ↓
Final Answer
```

Responsibilities are intentionally separated:

- `AgentConfig`: model and API connection configuration.
- `AgentState`: mutable state for one agent run: original task, history, current step, metadata.
- `ContextManager`: creates state, rebuilds model input, and records model/tool outputs.
- `CodingAgent`: decides when to call the model and tools; it no longer owns the raw history list.
- `Workspace`: filesystem boundary.
- `CodingTools`: `list_files`, `read_file`, `write_file`, `run_command`.

v0.3 does **not** compress context yet. It only establishes the state/context boundary that v0.4 will extend.

## Install

Python 3.10+ is required.

```bash
python -m venv .venv
pip install -e ".[dev]"
```

## Model and API configuration

Configuration precedence:

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

CLI overrides:

```bash
coding-agent "Add a /health endpoint" \
  --workspace ./my-project \
  --api-key your-key \
  --base-url https://example.com/v1 \
  --model your-model \
  --max-steps 12
```

Prefer `OPENAI_API_KEY` over `--api-key`, because command-line arguments can be stored in shell history or exposed to process inspection.

Built-in defaults:

```text
model: gpt-6-sol
max_steps: 20
```

## Context model

Every `CodingAgent.run(...)` creates a fresh `AgentState`.

Conceptually:

```text
AgentState
├── task
├── history
├── step
└── metadata
```

The `ContextManager` is currently deliberately simple:

```text
create_state(task)
build_input(state)
record_model_output(state, output)
record_tool_result(state, ...)
advance_step(state)
```

In v0.4, context compression will be added behind this boundary instead of being embedded directly into the Agent Loop.

## Tests

```bash
pytest
```

Unit tests do not call a real LLM API. The Agent Loop test uses a fake client.
GitHub Actions runs `pytest -q` on pushes to `main` and pull requests.

## Safety limits

This is **not a sandbox**.

- File paths are confined to the configured workspace.
- Absolute paths and `../` path escapes are rejected.
- Commands run without a shell and executable names are allow-listed.
- Git is limited to `status`, `diff`, `log`, and `show`.
- Commands time out and stdout/stderr are truncated.
- Allow-listed interpreters such as Python can still execute arbitrary code with the current user's OS permissions.
- API keys stay in process memory and are hidden from `AgentConfig.__repr__`.

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

v0.3 does not yet include context compression, multi-agent orchestration, RAG, vector databases, DAG execution, MCP, a web UI, Docker sandboxing, or automatic Git commit/push.
