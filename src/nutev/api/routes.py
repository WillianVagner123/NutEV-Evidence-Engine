from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from nutev.api.loaders import filter_df, list_artifacts, paginate_df, read_csv_safe, read_json_safe, read_markdown_safe, read_xlsx_safe
from nutev.review.human_review import append_human_review_decision, load_human_review_decisions, merge_human_review_decisions
from nutev.provider_settings import (
    load_provider_registry,
    load_provider_settings,
    masked_provider_settings,
    resolve_provider_secret,
    save_provider_settings,
)


def build_router(project_root: Path) -> APIRouter:
    r = APIRouter()

    @r.get("/", response_class=HTMLResponse)
    def index():
        t = (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
        return t

    @r.get("/api/health")
    def health():
        return {"status": "ok", "project_root": str(project_root), "service": "nutev-platform"}

    @r.get("/api/run-summary")
    def run_summary():
        return read_json_safe(project_root / "07_logs" / "run_summary.json")

    @r.get("/api/evidence")
    def evidence(limit: int = 100, offset: int = 0, lens: str | None = None, domain: str | None = None, condition: str | None = None, diet_pattern: str | None = None, outcome: str | None = None):
        df = read_xlsx_safe(project_root / "06_tables" / "NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx")
        if df.empty:
            df = read_csv_safe(project_root / "02_metadata" / "metadata_master.csv")
        df = filter_df(df, {"evidence_lenses": lens, "domains": domain, "clinical_conditions": condition, "diet_patterns": diet_pattern, "outcomes": outcome})
        return paginate_df(df, limit, offset)

    @r.get("/api/claims")
    def claims(limit: int = 100, offset: int = 0, claim_status: str | None = None, human_validation_status: str | None = None, evidence_type: str | None = None, needs_human_review: bool | None = None):
        df = read_csv_safe(project_root / "02_metadata" / "NUTEV_EVIDENCE_CLAIMS.csv")
        if df.empty:
            df = read_xlsx_safe(project_root / "06_tables" / "NUTEV_EVIDENCE_CLAIMS.xlsx")
        df = filter_df(df, {"claim_status": claim_status, "human_validation_status": human_validation_status, "evidence_type": evidence_type})
        if needs_human_review is not None and "needs_human_review" in df.columns:
            df = df[df["needs_human_review"].astype(str).str.lower().isin([str(needs_human_review).lower()])]
        return paginate_df(df, limit, offset)

    @r.get("/api/recommendations")
    def recommendations(limit: int = 100, offset: int = 0, recommendation_status: str | None = None, human_approval_status: str | None = None, protocol_component: str | None = None):
        df = read_csv_safe(project_root / "02_metadata" / "NUTEV_RECOMMENDATION_CANDIDATES.csv")
        if df.empty:
            df = read_xlsx_safe(project_root / "06_tables" / "NUTEV_RECOMMENDATION_CANDIDATES.xlsx")
        df = filter_df(df, {"recommendation_status": recommendation_status, "human_approval_status": human_approval_status, "protocol_component": protocol_component})
        return paginate_df(df, limit, offset)

    @r.get("/api/human-review-queue")
    def human_review_queue(limit: int = 200, offset: int = 0):
        df = read_xlsx_safe(project_root / "06_tables" / "NUTEV_HUMAN_REVIEW_QUEUE.xlsx")
        if df.empty:
            df = read_csv_safe(project_root / "06_tables" / "NUTEV_HUMAN_REVIEW_QUEUE.csv")
        ddf = load_human_review_decisions(project_root)
        merged = merge_human_review_decisions(df, ddf)
        return paginate_df(merged, limit, offset)

    @r.get("/api/human-review-decisions")
    def human_review_decisions(limit: int = 200, offset: int = 0):
        return paginate_df(load_human_review_decisions(project_root), limit, offset)

    @r.post("/api/human-review-decisions")
    def human_review_decisions_post(payload: dict):
        append_human_review_decision(project_root, payload)
        latest = load_human_review_decisions(project_root).tail(1)
        return latest.to_dict("records")[0] if not latest.empty else {"available": False}

    @r.get("/api/artifacts")
    def artifacts():
        return {"available": True, "items": list_artifacts(project_root)}

    @r.get("/api/methods")
    def methods():
        text = read_markdown_safe(project_root / "08_docs" / "NUTEV_METHODS_MASTER.md")
        if not text:
            return {"available": False, "message": "Methods document not generated yet."}
        return {"available": True, "markdown": text}

    @r.get("/api/providers")
    def providers():
        reg = load_provider_registry(Path("config"))
        return {"available": True, "items": reg.get("providers", [])}

    @r.get("/api/provider-settings")
    def provider_settings():
        return {"available": True, **masked_provider_settings(project_root)}

    @r.post("/api/provider-settings")
    def provider_settings_post(payload: dict):
        save_provider_settings(project_root, payload)
        return {"available": True, **masked_provider_settings(project_root)}

    @r.post("/api/provider-settings/test")
    def provider_settings_test(payload: dict):
        provider_id = str(payload.get("provider_id", ""))
        settings = load_provider_settings(project_root).get("providers", {}).get(provider_id, {})
        if not settings.get("enabled", False):
            return {"provider_id": provider_id, "status": "disabled", "message": "Provider disabled", "checked_at": __import__("datetime").datetime.now().isoformat()}
        env_var = settings.get("env_var", "")
        secret = resolve_provider_secret(provider_id, env_var, project_root)
        if provider_id in {"openai", "anthropic", "google_gemini", "openrouter", "brave_search", "serpapi"} and not secret:
            return {"provider_id": provider_id, "status": "missing_key", "message": "API key missing", "checked_at": __import__("datetime").datetime.now().isoformat()}
        if provider_id == "ollama":
            import requests
            try:
                base_url = settings.get("base_url", "http://127.0.0.1:11434")
                resp = requests.get(f"{base_url}/api/tags", timeout=2)
                if resp.status_code == 200:
                    return {"provider_id": provider_id, "status": "ok", "message": "Ollama available", "checked_at": __import__("datetime").datetime.now().isoformat()}
                return {"provider_id": provider_id, "status": "provider_unavailable", "message": f"HTTP {resp.status_code}", "checked_at": __import__("datetime").datetime.now().isoformat()}
            except Exception:
                return {"provider_id": provider_id, "status": "provider_unavailable", "message": "Ollama not reachable", "checked_at": __import__("datetime").datetime.now().isoformat()}
        return {"provider_id": provider_id, "status": "ok", "message": "Provider minimally configured", "checked_at": __import__("datetime").datetime.now().isoformat()}

    @r.get("/api/provider-health")
    def provider_health():
        reg = load_provider_registry(Path("config")).get("providers", [])
        settings = load_provider_settings(project_root).get("providers", {})
        items = []
        for p in reg:
            pid = p.get("provider_id")
            cfg = settings.get(pid, {})
            items.append({
                "provider_id": pid,
                "enabled": bool(cfg.get("enabled", p.get("default_enabled", False))),
                "mode": cfg.get("mode", "disabled"),
                "secret_status": "configured" if resolve_provider_secret(pid, cfg.get("env_var", ""), project_root) else "missing",
            })
        return {"available": True, "items": items}

    return r
