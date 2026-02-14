from __future__ import annotations

from typing import Dict

from prophet_cli.core.errors import ProphetError

from .contracts import GenerationContext
from .contracts import StackGenerator


def run_generation_pipeline(
    context: GenerationContext,
    generators: Dict[str, StackGenerator],
) -> Dict[str, str]:
    if context.stack_id not in generators:
        supported = ", ".join(sorted(generators.keys())) or "none"
        raise ProphetError(
            f"Stack '{context.stack_id}' is declared but no generator implementation is registered. "
            f"Implemented stacks: {supported}."
        )
    return generators[context.stack_id](context)

