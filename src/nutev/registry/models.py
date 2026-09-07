from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RegistryAlias:
    """One observed exact alias for a durable article identity."""

    scheme: str
    normalized_value: str
    raw_value: str = ""
    provider: str = ""


@dataclass(frozen=True, slots=True)
class ArticleRegistration:
    """Result of registering one observed article manifestation."""

    status: str
    article_id: str | None
    created: bool = False
    enriched: bool = False
    conflict_id: str | None = None
    matched_article_ids: tuple[str, ...] = field(default_factory=tuple)
    aliases_added: int = 0
    manifestation_added: bool = False


@dataclass(frozen=True, slots=True)
class RegistryStats:
    """Operational registry counts; none of these imply scientific inclusion."""

    articles: int
    aliases: int
    manifestations: int
    search_runs: int
    search_hits: int
    identity_conflicts_open: int
