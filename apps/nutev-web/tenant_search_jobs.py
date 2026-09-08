from __future__ import annotations

import copy
import threading
import time
from typing import Any
from uuid import uuid4

from nutev.tenancy import Principal, ResearchContext, SearchScopeService
from query_compiler import compile_query_plan
from search_adapter import PROVIDER_LABELS
from server import (
    _SEARCH_JOBS,
    _SEARCH_JOBS_LOCK,
    _load_search_job,
    _now,
    _prune_jobs_locked,
    _run_search_job,
    _selected_providers,
)
from tenant_platform_routes import install_tenant_platform_routes

SEARCH_OWNER_WATCH_INTERVAL_SECONDS = 0.25

# SecureNutEVHandler imports this module and delegates unknown routes to NutEVHandler.
# Install authenticated tenant-platform extensions on that shared base handler once.
install_tenant_platform_routes()


def create_tenant_search_job(
    payload: dict[str, object],
    *,
    principal: Principal,
    context: ResearchContext,
    scope_service: SearchScopeService,
) -> dict[str, object]:
    """Create ownership first and only then start the background search worker."""

    scope_service.authorize_new_search(principal, context)
    providers = _selected_providers(payload)
    query = str(payload.get("query") or "").strip()
    if not query:
        raise ValueError("A pergunta de busca não pode ficar vazia.")
    per_provider = int(payload.get("per_provider", 25))
    max_results = int(payload.get("max_results", 100))
    query_plan = compile_query_plan(query, providers, payload.get("strategy"))

    job_id = "job_" + uuid4().hex
    job: dict[str, object] = {
        "job_id": job_id,
        "search_id": None,
        "status": "queued",
        "stage": "queued",
        "query": query,
        "query_plan": query_plan,
        "created_at": _now(),
        "updated_at": _now(),
        "completed_providers": 0,
        "total_providers": len(providers),
        "providers": [
            {
                "provider": provider,
                "label": PROVIDER_LABELS[provider],
                "status": "queued",
                "returned": 0,
                "total_found": None,
                "error": "",
            }
            for provider in providers
        ],
        "tenant_scope": {
            "workspace_id": context.workspace_id,
            "project_id": context.project_id,
        },
        "result": None,
        "error": None,
    }

    with _SEARCH_JOBS_LOCK:
        _prune_jobs_locked()
        _SEARCH_JOBS[job_id] = job

    try:
        scope_service.record_new_job(
            principal,
            context,
            job_id=job_id,
        )
    except Exception:
        with _SEARCH_JOBS_LOCK:
            _SEARCH_JOBS.pop(job_id, None)
        raise

    thread = threading.Thread(
        target=_run_search_job,
        kwargs={
            "job_id": job_id,
            "query": query,
            "providers": providers,
            "per_provider": per_provider,
            "max_results": max_results,
            "query_plan": query_plan,
        },
        name=f"nutev-tenant-search-{job_id[-8:]}",
        daemon=True,
    )
    thread.start()
    return copy.deepcopy(job)


def bind_tenant_search_when_terminal(job_id: str, scope_service: SearchScopeService) -> None:
    while True:
        try:
            job = _load_search_job(job_id)
        except KeyError:
            return
        status = str(job.get("status") or "")
        if status == "failed":
            return
        if status == "completed":
            search_id = str(job.get("search_id") or "").strip()
            if search_id:
                try:
                    scope_service.store.bind_search(job_id=job_id, search_id=search_id)
                except Exception:
                    # Fail closed: an unbound result remains invisible to authenticated history.
                    with _SEARCH_JOBS_LOCK:
                        live = _SEARCH_JOBS.get(job_id)
                        if live is not None:
                            live["ownership_status"] = "tenant_bind_failed"
                    return
                with _SEARCH_JOBS_LOCK:
                    live = _SEARCH_JOBS.get(job_id)
                    if live is not None:
                        live["ownership_status"] = "tenant_bound"
            return
        time.sleep(SEARCH_OWNER_WATCH_INTERVAL_SECONDS)


def start_tenant_search_owner_watch(job_id: str, scope_service: SearchScopeService) -> None:
    thread = threading.Thread(
        target=bind_tenant_search_when_terminal,
        args=(job_id, scope_service),
        name=f"nutev-tenant-search-owner-{job_id[-8:]}",
        daemon=True,
    )
    thread.start()


def load_tenant_search_job(
    job_id: str,
    *,
    principal: Principal,
    context: ResearchContext,
    scope_service: SearchScopeService,
) -> dict[str, Any]:
    owner = scope_service.require_job_access(principal, context, job_id)
    job = _load_search_job(job_id)
    payload = dict(job)
    payload["tenant_scope"] = {
        "workspace_id": owner.workspace_id,
        "project_id": owner.project_id,
    }
    payload["created_by_current_user"] = owner.user_id == principal.user_id
    return payload
