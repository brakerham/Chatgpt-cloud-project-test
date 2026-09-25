from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from coding_agent.agent import CodingAgent


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
