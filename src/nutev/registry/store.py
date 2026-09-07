from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from .models import ArticleRegistration, RegistryStats


class ArticleRegistryStore(Protocol):
    """Storage contract for durable NutEV article identity."""

    @property
    def database_path(self) -> Path: ...

    def register_article(
        self,
        record: dict[str, Any],
        *,
        provider: str = "",
        observed_at: str | None = None,
    ) -> ArticleRegistration: ...

    def get_article(self, article_id: str) -> dict[str, Any] | None: ...

    def stats(self) -> RegistryStats: ...

    def integrity_check(self) -> str: ...
