from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Protocol

from prophet_cli.core.ir_reader import IRReader


@dataclass(frozen=True)
class GenerationContext:
    stack_id: str
    ir: Dict[str, Any]
    ir_reader: IRReader
    cfg: Dict[str, Any]
    root: Path


class StackGenerator(Protocol):
    def __call__(self, context: GenerationContext) -> Dict[str, str]:
        ...
