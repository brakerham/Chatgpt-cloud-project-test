from __future__ import annotations

import argparse
import os
from pathlib import Path

from .agent import DEFAULT_MODEL, CodingAgent


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
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help=f"OpenAI model ID. Default: OPENAI_MODEL or {DEFAULT_MODEL}.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    agent = CodingAgent(workspace=args.workspace, model=args.model)
    print(agent.run(args.task))


if __name__ == "__main__":
    main()
