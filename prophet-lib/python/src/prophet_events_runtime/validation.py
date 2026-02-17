from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TransitionValidationResult:
    passesValidation: bool
    failureReason: Optional[str] = None

    @classmethod
    def passed(cls) -> "TransitionValidationResult":
        return cls(passesValidation=True, failureReason=None)

    @classmethod
    def failed(cls, failure_reason: str) -> "TransitionValidationResult":
        return cls(passesValidation=False, failureReason=failure_reason)
