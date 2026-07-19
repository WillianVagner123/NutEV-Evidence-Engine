"""Article-1 web API (§15): serves the reproducible pipeline outputs as JSON.

Read-only endpoints over the artifacts the ``nutev guides`` pipeline already
writes (denominators, PRISMA counts, the A/B/C/D matrix, evidence gems, domain
states, the two-reviewer screening queue and the entity registries). This is the
foundation the §15 web modules consume — no database required yet; everything is
derived from the on-disk, reproducible outputs.

Every payload keeps the scientific caveats explicit (assistive coding, no final
corpus, descriptive value only) so the UI can surface them.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from nutev.api.loaders import paginate_df, read_csv_safe, read_json_safe

_ASSISTIVE_NOTE = (
    "Codificação assistiva (sugestão de máquina), sob revisão humana. "
    "Nenhum corpus final é declarado e nada aqui avalia qualidade/risco de viés."
)


def build_article1_router(project_root: Path) -> APIRouter:
    r = APIRouter(prefix="/api/article1", tags=["article1"])
    tables = project_root / "06_tables"
    logs = project_root / "07_logs"

    @r.get("/guides-summary")
    def guides_summary():
        return {"note": _ASSISTIVE_NOTE, **read_json_safe(logs / "guides_summary.json")}

    @r.get("/denominators")
    def denominators():
        df = read_csv_safe(logs / "denominator_registry.csv")
        return {"note": "Denominadores nomeados — nunca somar/intercambiar (§7.1).",
                "items": df.fillna("").to_dict("records")}

    @r.get("/prisma")
    def prisma():
        return read_json_safe(logs / "prisma_counts.json")

    @r.get("/abcd-matrix")
    def abcd_matrix(limit: int = 200, offset: int = 0):
        out = paginate_df(read_csv_safe(tables / "NUTEV_GUIDES_ABCD_MATRIX.csv"), limit, offset)
        out["note"] = _ASSISTIVE_NOTE
        return out

    @r.get("/domain-states")
    def domain_states(limit: int = 500, offset: int = 0, state: str | None = None, domain: str | None = None):
        df = read_csv_safe(tables / "NUTEV_GUIDES_DOMAIN_STATES.csv")
        if state and "state" in df.columns:
            df = df[df["state"].astype(str) == state]
        if domain and "domain" in df.columns:
            df = df[df["domain"].astype(str) == domain]
        out = paginate_df(df, limit, offset)
        out["note"] = _ASSISTIVE_NOTE
        return out

    @r.get("/gems")
    def gems(limit: int = 100, offset: int = 0):
        out = paginate_df(read_csv_safe(tables / "NUTEV_GUIDES_EVIDENCE_GEMS.csv"), limit, offset)
        out["note"] = "Valor descritivo (score 0–18) — NÃO é avaliação de qualidade/risco de viés (§14)."
        return out

    @r.get("/screening-queue")
    def screening_queue(limit: int = 500, offset: int = 0, flag: str | None = None):
        df = read_csv_safe(tables / "NUTEV_GUIDES_SCREENING_QUEUE.csv")
        if flag and "screen_flag" in df.columns:
            df = df[df["screen_flag"].astype(str) == flag]
        out = paginate_df(df, limit, offset)
        out["note"] = "Fila de dois revisores — nada é export_ready até validação humana (§13)."
        return out

    @r.get("/families")
    def families():
        return {"items": read_csv_safe(logs / "document_family_registry.csv").fillna("").to_dict("records")}

    @r.get("/versions")
    def versions():
        return {"items": read_csv_safe(logs / "document_version_registry.csv").fillna("").to_dict("records")}

    @r.get("/dashboard", response_class=HTMLResponse)
    def dashboard():
        return (Path(__file__).parent / "templates" / "article1.html").read_text(encoding="utf-8")

    return r
