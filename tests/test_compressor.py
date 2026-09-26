from types import SimpleNamespace

from coding_agent.context.compressor import ContextCompressor


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="- Goal\nContinue the task.")


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def test_compressor_calls_model_without_tools() -> None:
    client = FakeClient()
    compressor = ContextCompressor(client=client, model="test-model")

    result = compressor.compress(
        task="Fix the project",
        previous_summary="Earlier work",
        history_text="pytest failed in tests/test_app.py",
    )

    assert result == "- Goal\nContinue the task."
    assert len(client.responses.calls) == 1

    call = client.responses.calls[0]
    assert call["model"] == "test-model"
    assert call["store"] is False
    assert "tools" not in call

    payload = call["input"][0]["content"]
    assert "Fix the project" in payload
    assert "Earlier work" in payload
    assert "pytest failed" in payload
