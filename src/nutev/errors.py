"""Typed error hierarchy for classified, non-silent failures.

Scientific collection must keep running when one provider or document fails —
but the failure has to be *classified*, not swallowed. Each error carries a
stable ``code`` plus the context needed to reason about lost coverage: provider,
query, pipeline stage, whether it is recoverable, the attempt number, any
fallback used, and the coverage impact.

Pair with :mod:`nutev.telemetry.coverage` to turn caught failures into an
auditable "lost coverage" report instead of ``except Exception: pass``.
"""
from __future__ import annotations


class NutEVError(Exception):
    """Base for all classified NutEV failures. Subclasses set a stable ``code``."""

    code = "nutev_error"

    def __init__(
        self,
        message: str = "",
        *,
        provider: str = "",
        query: str = "",
        stage: str = "",
        recoverable: bool = True,
        attempt: int = 0,
        fallback_used: str = "",
        coverage_impact: str = "",
    ) -> None:
        super().__init__(message or self.code)
        self.message = message or self.code
        self.provider = provider
        self.query = query
        self.stage = stage
        self.recoverable = recoverable
        self.attempt = attempt
        self.fallback_used = fallback_used
        self.coverage_impact = coverage_impact

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "provider": self.provider,
            "query": self.query,
            "stage": self.stage,
            "recoverable": self.recoverable,
            "attempt": self.attempt,
            "fallback_used": self.fallback_used,
            "coverage_impact": self.coverage_impact,
        }


class ProviderUnavailableError(NutEVError):
    """A search provider could not be reached (network/DNS/5xx)."""

    code = "provider_unavailable"


class ProviderRateLimitError(NutEVError):
    """A provider rejected the request for rate limiting (429/backoff)."""

    code = "provider_rate_limit"


class InvalidProviderResponseError(NutEVError):
    """A provider responded but the payload could not be parsed/normalized."""

    code = "invalid_provider_response"


class DocumentExtractionError(NutEVError):
    """A document could not be extracted to text."""

    code = "document_extraction_error"


class OCRRequiredError(DocumentExtractionError):
    """Extraction needs OCR but the OCR prerequisites are unavailable."""

    code = "ocr_required"


class ArtifactContractError(NutEVError):
    """An output artifact violated its expected schema/contract."""

    code = "artifact_contract_error"
