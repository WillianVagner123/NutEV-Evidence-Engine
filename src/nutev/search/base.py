from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ProviderResult:
    provider: str
    query: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    total_found: int | None = None
    total_returned: int = 0
    status: str = "completed"
    error: str | None = None
    checkpoint_path: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


class ProviderClient(Protocol):
    name: str

    def search(
        self,
        query: str,
        *,
        limit: int,
        context: dict[str, Any] | None = None,
    ) -> ProviderResult:
        ...
