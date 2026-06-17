from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from nutev.api.loaders import filter_df, list_artifacts, paginate_df, read_csv_safe, read_json_safe, read_markdown_safe, read_xlsx_safe, tail_jsonl
from nutev.api.schemas import HumanReviewDecisionIn, RunRequest
from nutev.review.human_review import append_human_review_decision, load_human_review_decisions, merge_human_review_decisions

# Workstreams the "Play" button may launch. Args are passed to subprocess as a
# list (no shell), and validated against this set, so user input can't inject.
VALID_WORKSTREAMS = {"busca1", "busca2a", "busca2b", "a3", "article3", "artigo3_framework"}


def build_router(project_root: Path) -> APIRouter:
    r = APIRouter()
    # Single in-process handle to the pipeline launched from the UI. The server
    # is local-first (127.0.0.1), so one run at a time is the intended model.
    run_state: dict = {"proc": None, "started_at": None, "workstreams": [], "options": {}}

    def _run_status() -> dict:
        proc = run_state["proc"]
        returncode = proc.poll() if proc is not None else None
        return {
            "running": proc is not None and returncode is None,
            "pid": proc.pid if proc is not None else None,
            "returncode": returncode,
            "started_at": run_state["started_at"],
            "workstreams": run_state["workstreams"],
            "options": run_state["options"],
            "log": "07_logs/serve_run.log",
        }

    @r.get("/", response_class=HTMLResponse)
    def index():
        t = (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
        return t

    @r.get("/api/run/status")
    def run_status():
        return _run_status()

    @r.post("/api/run")
    def run_start(payload: RunRequest | None = None):
        if run_state["proc"] is not None and run_state["proc"].poll() is None:
            raise HTTPException(status_code=409, detail="A pipeline run is already in progress")
        body = payload or RunRequest()
        workstreams = body.workstreams or ["busca1"]
        invalid = [w for w in workstreams if w not in VALID_WORKSTREAMS]
        if invalid:
            raise HTTPException(status_code=422, detail=f"Invalid workstreams {invalid}; allowed: {sorted(VALID_WORKSTREAMS)}")

        args = [sys.executable, "-m", "nutev", "--project-root", str(project_root), "--workstreams", *workstreams]
        if getattr(sys, "frozen", False):
            # Packaged app: sys.executable is the NutEV exe (no '-m'); re-invoke
            # it with pipeline args, which the app entry routes to the CLI.
            args = [sys.executable, "--project-root", str(project_root), "--workstreams", *workstreams]
        env = dict(os.environ)
        if getattr(sys, "frozen", False):
            # A one-file PyInstaller child must not inherit the parent's
            # bootloader vars, or it reuses the parent's extraction and fails.
            for _k in ("_MEIPASS2", "_PYI_APPLICATION_HOME_DIR", "_PYI_ARCHIVE_FILE", "_PYI_PARENT_PROCESS_LEVEL"):
                env.pop(_k, None)
        if body.web_enabled:
            args.append("--web-enabled")
            env.pop("NUTEV_DISABLE_NETWORK", None)
        else:
            env["NUTEV_DISABLE_NETWORK"] = "1"  # default: safe offline run
        if body.journal_quality:
            env["NUTEV_JOURNAL_QUALITY"] = "1"

        logs_dir = project_root / "07_logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_fh = open(logs_dir / "serve_run.log", "ab")
        proc = subprocess.Popen(args, stdout=log_fh, stderr=subprocess.STDOUT, env=env)
        run_state.update({
            "proc": proc,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "workstreams": workstreams,
            "options": {"web_enabled": bool(body.web_enabled), "journal_quality": bool(body.journal_quality)},
        })
        return {"started": True, **_run_status()}

    @r.post("/api/run/stop")
    def run_stop():
        proc = run_state["proc"]
        if proc is None or proc.poll() is not None:
            return {"stopped": False, "message": "No run in progress"}
        proc.terminate()
        return {"stopped": True, "pid": proc.pid}

    @r.get("/api/health")
    def health():
        return {"status": "ok", "project_root": str(project_root), "service": "nutev-platform"}

    @r.get("/api/run-summary")
    def run_summary():
        return read_json_safe(project_root / "07_logs" / "run_summary.json")

    @r.get("/api/run-events")
    def run_events(limit: int = 120, offset: int = 0):
        # Live monitor feed. Poll with ?offset=<previous total> to stream only
        # new events as a run progresses (run_events.jsonl is appended live).
        return tail_jsonl(project_root / "07_logs" / "run_events.jsonl", limit, offset)

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
    def human_review_decisions_post(payload: HumanReviewDecisionIn):
        # Typed body => FastAPI returns 422 on malformed input; domain-rule
        # violations (invalid item_type/role/decision) raise ValueError, which
        # we surface as 422 rather than letting it become a 500.
        try:
            append_human_review_decision(project_root, payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        latest = load_human_review_decisions(project_root).tail(1)
        return latest.to_dict("records")[0] if not latest.empty else {"available": False}

    @r.get("/api/artifacts")
    def artifacts():
        return {"available": True, "items": list_artifacts(project_root)}

    @r.get("/api/provider-health")
    def provider_health():
        # Advertised on the landing page; reports env-based provider/model
        # configuration status (parity with the Streamlit Provider Settings page).
        providers = [
            "openai", "anthropic", "google_gemini", "openrouter", "ollama",
            "brave_search", "serpapi", "ncbi_pubmed", "crossref", "openalex", "europepmc",
        ]
        assistive = {"openai", "anthropic", "google_gemini", "openrouter", "ollama"}
        items = []
        for provider in providers:
            env_name = provider.upper() + ("_EMAIL" if provider in {"crossref", "openalex"} else "_API_KEY")
            items.append({
                "provider": provider,
                "secret_source": "env",
                "secret_status": "configured" if os.environ.get(env_name) else "missing",
                "mode": "assistive" if provider in assistive else "lookup",
            })
        return {"available": True, "items": items}

    @r.get("/api/methods")
    def methods():
        text = read_markdown_safe(project_root / "08_docs" / "NUTEV_METHODS_MASTER.md")
        if not text:
            return {"available": False, "message": "Methods document not generated yet."}
        return {"available": True, "markdown": text}

    return r
