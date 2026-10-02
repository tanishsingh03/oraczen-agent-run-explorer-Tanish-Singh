from abc import ABC, abstractmethod
from typing import AsyncIterator

class ExplainProvider(ABC):
    @abstractmethod
    async def explain(self, run: dict) -> AsyncIterator[str]:
        ...
