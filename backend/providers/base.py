"""
providers/base.py — Abstract base class for explain providers.

WHY an abstract base class instead of a plain function?
  The mock and real providers share the same calling convention.
  An ABC enforces that contract at import time — if someone adds a
  third provider and forgets to implement explain(), Python raises
  TypeError immediately rather than at runtime when a user clicks the button.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator


class ExplainProvider(ABC):
    @abstractmethod
    async def explain(self, run: dict) -> AsyncIterator[str]:
        """
        Given a full run dict, yield text chunks suitable for SSE streaming.
        Must be deterministic for the mock provider (same run → same text).
        """
        ...
