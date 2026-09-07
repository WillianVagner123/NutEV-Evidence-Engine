"""Cumulative NutEV Article Registry.

The registry owns durable article identity. Search runs only discover and reference
articles; scientific inclusion, quality, certainty, recommendations, and PRISMA
state remain separate downstream concerns.
"""

from .models import ArticleRegistration, RegistryAlias, RegistryStats
from .sqlite_store import SQLiteArticleRegistry

__all__ = [
    "ArticleRegistration",
    "RegistryAlias",
    "RegistryStats",
    "SQLiteArticleRegistry",
]
