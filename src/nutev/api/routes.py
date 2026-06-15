from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from nutev.api.loaders import filter_df, list_artifacts, paginate_df, read_csv_safe, read_json_safe, read_markdown_safe, read_xlsx_safe
from nutev.api.schemas import HumanReviewDecisionIn
from nutev.review.human_review import append_human_review_decision, load_human_review_decisions, merge_human_review_decisions


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

    @r.get("/api/methods")
    def methods():
        text = read_markdown_safe(project_root / "08_docs" / "NUTEV_METHODS_MASTER.md")
        if not text:
            return {"available": False, "message": "Methods document not generated yet."}
        return {"available": True, "markdown": text}

    return r
