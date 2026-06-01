from __future__ import annotations


class ProviderError(RuntimeError):
    """Base class for recoverable provider errors."""


class ProviderSkipped(ProviderError):
    """Raised when an optional provider is intentionally skipped."""
