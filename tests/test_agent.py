from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from coding_agent.agent import CodingAgent
from coding_agent.context import ContextManager


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._responses = iter(
            [
                SimpleNamespace(
                    output=[
                        SimpleNamespace(
                            type="function_call",
                            name="write_file",
                            arguments=(
                                '{"path":"hello.py","content":"print(\\\"hello\\\")\\n"}'
                            ),
                            call_id="call_1",
                        )
                    ],
                    output_text="",
                ),
                SimpleNamespace(
                    output=[SimpleNamespace(type="message")],
                    output_text="Created hello.py.",
                ),
            ]
        )

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return next(self._responses)


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class FakeCompressor:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def compress(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return "The agent already created hello.py."


def test_agent_executes_tool_call_and_returns_final_text(tmp_path: Path) -> None:
    client = FakeClient()
    agent = CodingAgent(workspace=tmp_path, client=client)

    result = agent.run("Create hello.py")

    assert result == "Created hello.py."
    assert (tmp_path / "hello.py").read_text(encoding="utf-8") == 'print("hello")\n'
    assert len(client.responses.calls) == 2

    second_input = client.responses.calls[1]["input"]
    tool_outputs = [
        item
        for item in second_input
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    ]
    assert len(tool_outputs) == 1
    assert tool_outputs[0]["call_id"] == "call_1"


def test_agent_continues_after_context_compression(tmp_path: Path) -> None:
    client = FakeClient()
    compressor = FakeCompressor()
    context = ContextManager(max_context_chars=1, recent_items=0)
    agent = CodingAgent(
        workspace=tmp_path,
        client=client,
        context_manager=context,
        compressor=compressor,
    )

    result = agent.run("Create hello.py")

    assert result == "Created hello.py."
    assert len(compressor.calls) == 1

    second_input = client.responses.calls[1]["input"]
    assert second_input[0] == {"role": "user", "content": "Create hello.py"}
    assert "already created hello.py" in second_input[1]["content"]

    # Old function-call protocol items were compacted instead of being partially replayed.
    assert not any(
        isinstance(item, dict) and item.get("type") == "function_call_output"
        for item in second_input
    )
