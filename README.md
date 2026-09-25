# Minimal Coding Agent

A deliberately small, single-agent coding assistant for learning the core agent loop.

## How it works

```text
User Task
  -> LLM
  -> Tool Call
  -> Tool Execution
  -> Tool Result
  -> LLM
  -> ...
  -> Final Answer
```

The model has only four tools:

- `list_files`
- `read_file`
- `write_file`
- `run_command`

`Workspace` owns the filesystem boundary. `CodingAgent` owns the model/tool loop.

## Install

Python 3.10+ is required.

```bash
python -m venv .venv
pip install -e ".[dev]"
```

Set an OpenAI API key:

PowerShell:

```powershell
$env:OPENAI_API_KEY="your-key"
```

bash/zsh:

```bash
export OPENAI_API_KEY="your-key"
```

## Run

```bash
coding-agent "Create a hello world Python program and run it"
```

Choose a workspace and model:

```bash
coding-agent "Add a /health endpoint" --workspace ./my-project --model gpt-6-sol
```

The default model is `gpt-6-sol`. Set `OPENAI_MODEL` or pass `--model` to override it.

The workspace directory must already exist.

## Tests

```bash
pytest
```

Unit tests do not call the OpenAI API. The Agent Loop test uses a fake client.

## Safety limits

This is **not a sandbox**.

- File paths are confined to the configured workspace.
- Absolute paths and `../` path escapes are rejected.
- Commands run without a shell and executable names are allow-listed.
- Git is limited to `status`, `diff`, `log`, and `show`.
- Commands time out and stdout/stderr are truncated.
- Allow-listed interpreters such as Python can still execute arbitrary code with the current user's OS permissions.

Use an isolated test workspace for untrusted tasks.

## Intentionally not implemented

The v0.1 project does not include multi-agent orchestration, planner/reviewer agents, memory, RAG, vector databases, DAG execution, MCP, a web UI, Docker sandboxing, or automatic Git commit/push.
