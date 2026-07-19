"""Single source of truth for provider metadata (`config/provider_registry.json`).

Before this loader, that registry file existed but nothing read it: the UI
invented credential environment-variable names by convention
(``PROVIDER.upper() + "_API_KEY"``), producing wrong names — e.g. it looked for
``NCBI_PUBMED_API_KEY`` / ``CROSSREF_EMAIL`` / ``OPENALEX_EMAIL`` while the code
actually uses ``NCBI_API_KEY`` / ``CROSSREF_MAILTO`` / ``OPENALEX_MAILTO``. That
meant the dashboard could report a configured provider as "missing" (or vice
versa).

This module makes the registry the authority: the declared ``env_vars`` are the
real names, and the UI/health checks read them here instead of guessing.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from nutev.settings import default_config_root

# Provider types that only *assist* (LLMs / local models) — never approve.
_ASSISTIVE_TYPES = {"llm", "local_model"}


def load_provider_registry(config_root: Path | None = None) -> dict:
    """Load the provider registry JSON (defaults to the packaged config)."""
    root = Path(config_root) if config_root else default_config_root()
    path = root / "provider_registry.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"providers": []}


def list_providers(config_root: Path | None = None) -> list[dict]:
    return list(load_provider_registry(config_root).get("providers", []))


def declared_provider_ids(config_root: Path | None = None) -> set[str]:
    """All provider ids declared in the registry, including aliases."""
    declared: set[str] = set()
    for p in list_providers(config_root):
        pid = p.get("provider_id")
        if pid:
            declared.add(pid)
        declared.update(p.get("aliases", []))
    return declared


def reconcile_providers(implemented: list[str], config_root: Path | None = None) -> dict:
    """Cross-check implemented providers against the declared registry.

    Returns ``declared_not_implemented`` (in the config but with no code) and
    ``implemented_not_declared`` (code exists but the config never declared it —
    the drift the audit warned about). The registry is the single source of truth
    for *which providers exist*; a non-empty ``implemented_not_declared`` is a bug.
    """
    declared = declared_provider_ids(config_root)
    impl = set(implemented)
    # Only search-capable declared providers can be "not implemented"; LLM/local
    # models are declared but never run as search providers.
    search_declared = {
        p.get("provider_id") for p in list_providers(config_root)
        if p.get("provider_type") in {"search", "bibliographic", "official_source"}
    } | {a for p in list_providers(config_root)
         if p.get("provider_type") in {"search", "bibliographic", "official_source"}
         for a in p.get("aliases", [])}
    return {
        "declared_not_implemented": sorted(search_declared - impl),
        "implemented_not_declared": sorted(impl - declared),
    }


def provider_env_vars(provider_id: str, config_root: Path | None = None) -> list[str]:
    """Return the REAL credential env-var names for a provider (from the registry)."""
    for p in list_providers(config_root):
        if p.get("provider_id") == provider_id:
            return list(p.get("env_vars", []))
    return []


def _credential_status(env_vars: list[str], environ) -> str:
    """`not_required` when no creds; else `configured` iff every declared var is set."""
    if not env_vars:
        return "not_required"
    return "configured" if all(environ.get(v) for v in env_vars) else "missing"


def provider_credential_rows(config_root: Path | None = None, environ=None) -> list[dict]:
    """Rows for the UI/health view, computed from the registry (never inferred).

    Each row: ``provider``, ``label``, ``provider_type``, ``env_vars`` (the real
    names), ``secret_status`` (configured/missing/not_required) and ``mode``
    (assistive for LLM/local models, else lookup).
    """
    environ = environ if environ is not None else os.environ
    rows: list[dict] = []
    for p in list_providers(config_root):
        env_vars = list(p.get("env_vars", []))
        ptype = p.get("provider_type", "")
        rows.append({
            "provider": p.get("provider_id", ""),
            "label": p.get("label", p.get("provider_id", "")),
            "provider_type": ptype,
            "env_vars": ", ".join(env_vars) if env_vars else "—",
            "secret_status": _credential_status(env_vars, environ),
            "mode": "assistive" if ptype in _ASSISTIVE_TYPES else "lookup",
        })
    return rows
