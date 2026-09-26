# Minimal Coding Agent

A deliberately small Coding Agent for learning the core agent runtime step by step.

Current version: **v0.4**

## Architecture

```text
User Task
   ↓
CodingAgent
   ↓
AgentState
   ↕
ContextManager
   │
   ├── normal history
   │
   └── when context grows too large
   │         ↓
   │   ContextCompressor
   │         ↓
   │   Summary + recent events
   ↓
LLM
   ↓
Tool Call
   ↓
CodingTools
   ↓
Tool Result
   ↓
...
```

Responsibilities:

- `AgentConfig`: API/model/runtime configuration.
- `AgentState`: task, active history, summary, recent compressed context, step count, metadata.
- `ContextManager`: builds model input, records events, measures context size, triggers compaction.
- `ContextCompressor`: uses the configured LLM to summarize older completed history.
- `CodingAgent`: Agent Loop orchestration.
- `Workspace`: filesystem boundary.
- `CodingTools`: file and command tools.

## Context compression

v0.4 uses a deliberately simple compaction strategy.

```text
Original task              always preserved
Older raw history          -> LLM structured summary
Most recent events         -> preserved as text
New events after compaction -> raw Responses history
```

When the active context exceeds the configured character budget:

1. the original user task is kept unchanged;
2. older model/tool history is serialized and summarized;
3. a limited number of the newest events are preserved as text;
4. old raw `function_call` / `function_call_output` protocol items are removed;
5. the next model call continues from the compacted context.

Removing completed tool protocol items as a unit avoids replaying a broken partial tool-call chain.

The summary prompt preserves:

- goal;
- completed work;
- files/artifacts;
- tests/checks;
- decisions and constraints;
- errors and unresolved issues;
- next likely action.

This version uses a **character budget**, not exact tokenizer accounting, to avoid adding another dependency.

Defaults:

```text
context_max_chars:   40000
context_recent_items: 8
```

Configure with environment variables:

```text
CODING_AGENT_CONTEXT_MAX_CHARS
CODING_AGENT_CONTEXT_RECENT_ITEMS
```

or CLI:

```bash
coding-agent "Implement the task" \
  --context-max-chars 50000 \
  --context-recent-items 6
```

A compression pass is an additional LLM call, so it consumes tokens/API usage.

## Install

Python 3.10+:

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
CODING_AGENT_CONTEXT_MAX_CHARS
CODING_AGENT_CONTEXT_RECENT_ITEMS
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

coding-agent "Inspect this project"
```

The endpoint must support the Responses API. Context compression also uses Responses API text generation.

Prefer environment variables over `--api-key` because command-line secrets may appear in shell history or process inspection.

## Tests

```bash
pytest
```

Tests do not call a real LLM API. Fake clients/compressors verify the Agent Loop and compaction behavior.
GitHub Actions runs `pytest -q` on pushes to `main` and pull requests.

## Safety limits

This is **not a sandbox**.

- Workspace path checks protect direct file tools.
- Commands run without a shell and executable names are allow-listed.
- Git is restricted to read-only subcommands.
- Commands have timeouts and truncated output.
- Interpreters such as Python can still access the host OS with the current user's permissions.
- API keys remain process-local and are hidden from `AgentConfig.__repr__`.

Use an isolated workspace for untrusted tasks.

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

v0.4 does not yet include SubAgents, DAG execution, RAG, vector databases, MCP, a web UI, Docker sandboxing, or automatic Git commit/push.
