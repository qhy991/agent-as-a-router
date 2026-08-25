#!/usr/bin/env python3
"""Build one formal, evidence-grounded Modus Router context and prompt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from acrouter_repro.modus_router_experience import (  # noqa: E402
    build_batch_context,
    build_batch_prompt,
    build_context,
    build_prompt,
    load_descriptor,
    load_registry,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=ROOT / "router/AGENTS.md")
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "configs/modus_profile_experience_registry.json",
    )
    parser.add_argument("--descriptor", type=Path, action="append", required=True)
    parser.add_argument("--context-output", type=Path, required=True)
    parser.add_argument("--prompt-output", type=Path, required=True)
    args = parser.parse_args()
    policy = args.policy.resolve()
    registry_path = args.registry.resolve()
    registry = load_registry(registry_path)
    descriptors = [load_descriptor(path.resolve()) for path in args.descriptor]
    contexts = [
        build_context(
            registry=registry,
            descriptor=descriptor,
            policy_path=policy,
            registry_path=registry_path,
        )
        for descriptor in descriptors
    ]
    batched = len(contexts) > 1
    context = build_batch_context(contexts) if batched else contexts[0]
    args.context_output.parent.mkdir(parents=True, exist_ok=True)
    args.prompt_output.parent.mkdir(parents=True, exist_ok=True)
    args.context_output.write_text(
        json.dumps(context, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    args.prompt_output.write_text(
        (
            build_batch_prompt(
                policy_text=policy.read_text(encoding="utf-8"), context=context
            )
            if batched else
            build_prompt(
                policy_text=policy.read_text(encoding="utf-8"), context=context
            )
        )
    )
    print(json.dumps({
        "task_ids": [descriptor["task_id"] for descriptor in descriptors],
        "relevant_experience": sum(
            len(item["relevant_experience"])
            for item in (
                context["tasks"] if batched
                else [{"relevant_experience": context["relevant_experience"]}]
            )
        ),
        "context_output": str(args.context_output),
        "prompt_output": str(args.prompt_output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
