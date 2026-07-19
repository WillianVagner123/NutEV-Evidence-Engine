"""Provider registry is the single source of truth for credential env names."""
from __future__ import annotations

from nutev.search.provider_registry import (
    provider_credential_rows,
    provider_env_vars,
)


def test_real_env_var_names_from_registry_not_convention():
    # The exact names the review flagged: convention would give the wrong ones.
    assert provider_env_vars("ncbi_pubmed") == ["NCBI_API_KEY", "NCBI_EMAIL"]
    assert provider_env_vars("crossref") == ["CROSSREF_MAILTO"]      # not CROSSREF_EMAIL
    assert provider_env_vars("openalex") == ["OPENALEX_MAILTO"]      # not OPENALEX_EMAIL


def test_credential_status_reflects_env():
    env = {"CROSSREF_MAILTO": "me@x.org"}  # crossref set, ncbi not
    rows = {r["provider"]: r for r in provider_credential_rows(environ=env)}
    assert rows["crossref"]["secret_status"] == "configured"
    assert rows["ncbi_pubmed"]["secret_status"] == "missing"
    # europepmc needs no credentials.
    assert rows["europepmc"]["secret_status"] == "not_required"


def test_mode_is_assistive_only_for_llm_and_local_models():
    rows = {r["provider"]: r for r in provider_credential_rows(environ={})}
    assert rows["openai"]["mode"] == "assistive"
    assert rows["ollama"]["mode"] == "assistive"          # local_model
    assert rows["ncbi_pubmed"]["mode"] == "lookup"        # bibliographic
    assert rows["crossref"]["mode"] == "lookup"


def test_rows_expose_real_names_string():
    rows = {r["provider"]: r for r in provider_credential_rows(environ={})}
    assert "CROSSREF_MAILTO" in rows["crossref"]["env_vars"]
    assert "NCBI_API_KEY" in rows["ncbi_pubmed"]["env_vars"]
    assert rows["europepmc"]["env_vars"] == "—"           # no creds
