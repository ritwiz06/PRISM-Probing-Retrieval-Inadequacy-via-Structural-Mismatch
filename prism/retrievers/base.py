from __future__ import annotations

from abc import ABC, abstractmethod

from prism.schemas import RetrievedItem


class BaseRetriever(ABC):
    backend_name: str

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedItem]:
        raise NotImplementedError
