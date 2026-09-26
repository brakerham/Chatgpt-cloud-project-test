from __future__ import annotations

import argparse
from pathlib import Path

from .agent import CodingAgent
from .config import AgentConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the minimal Coding Agent.")
    parser.add_argument("task", help="Coding task for the agent.")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("."),
        help="Project directory the agent may access. Default: current directory.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help=(
            "API key override. Prefer OPENAI_API_KEY so the key is not stored "
            "in shell history."
        ),
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible API base URL override.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model ID override.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Maximum model/tool loop steps.",
    )
    parser.add_argument(
        "--context-max-chars",
        type=int,
        default=None,
        help="Approximate context character budget before compression.",
    )
    parser.add_argument(
        "--context-recent-items",
        type=int,
        default=None,
        help="Maximum number of recent raw events preserved during compression.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = AgentConfig.from_sources(
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
        max_steps=args.max_steps,
        context_max_chars=args.context_max_chars,
        context_recent_items=args.context_recent_items,
    )
    agent = CodingAgent(workspace=args.workspace, config=config)
    print(agent.run(args.task))


if __name__ == "__main__":
    main()
