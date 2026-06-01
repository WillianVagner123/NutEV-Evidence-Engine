from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

PROVIDER_STATUSES = {"completed", "partial", "failed", "skipped", "empty"}


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

    def __post_init__(self) -> None:
        if self.status not in PROVIDER_STATUSES:
            raise ValueError(f"invalid provider status: {self.status}")
        self.total_returned = int(self.total_returned or len(self.rows or []))
        if self.status == "completed" and self.total_returned == 0 and self.total_found in {0, None}:
            self.status = "empty"


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
