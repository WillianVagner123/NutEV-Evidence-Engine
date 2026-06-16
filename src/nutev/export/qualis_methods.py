"""Publication-grade methodological artifacts for QUALIS A1 systematic reviews.

Generates, from a NutEV run, the reporting scaffolding that top-tier journals
require:

* PRISMA 2020 flow with per-database identified counts (NUTEV_PRISMA2020_FLOW.csv);
* a per-database search-strategy appendix with the exact executed queries
  (NUTEV_SEARCH_STRATEGY_APPENDIX.md) — reviewers must be able to reproduce each
  database search;
* a PROSPERO protocol template and the 27-item PRISMA 2020 checklist;
* a risk-of-bias template (RoB 2 / ROBINS-I / AMSTAR 2 domains) per document;
* a reproducibility report (run dates, source/tool versions, queries, and
  SHA-256 hashes of the configuration that drove the run).

These are scaffolding for the human researcher: they do not replace screening,
appraisal, adjudication or writing.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from nutev.export.metadata_tables import write_simple_csv
from nutev.utils import write_text

# Canonical PRISMA 2020 checklist (Page MJ et al., BMJ 2021;372:n71), 27 items.
PRISMA_2020_ITEMS: list[tuple[str, str, str]] = [
    ("TITLE", "1", "Identify the report as a systematic review."),
    ("ABSTRACT", "2", "See the PRISMA 2020 for Abstracts checklist."),
    ("INTRODUCTION", "3", "Rationale for the review in the context of existing knowledge."),
    ("INTRODUCTION", "4", "Explicit objective(s) or question(s) the review addresses."),
    ("METHODS", "5", "Eligibility criteria and how studies were grouped for synthesis."),
    ("METHODS", "6", "All databases/registers/sources searched, with dates."),
    ("METHODS", "7", "Full search strategy for all databases/registers/websites."),
    ("METHODS", "8", "Selection process (screeners, independence, automation tools)."),
    ("METHODS", "9", "Data collection process (extractors, independence, automation)."),
    ("METHODS", "10", "Data items: outcomes and all other variables sought."),
    ("METHODS", "11", "Study risk-of-bias assessment methods (tool, independence)."),
    ("METHODS", "12", "Effect measures used for each outcome in synthesis/presentation."),
    ("METHODS", "13", "Synthesis methods (eligibility, transformations, models)."),
    ("METHODS", "14", "Reporting bias assessment methods."),
    ("METHODS", "15", "Certainty assessment methods (e.g. GRADE)."),
    ("RESULTS", "16", "Study selection results and flow (PRISMA flow diagram)."),
    ("RESULTS", "17", "Cite each included study and present its characteristics."),
    ("RESULTS", "18", "Risk of bias of each included study."),
    ("RESULTS", "19", "Results of individual studies (effect estimates, CIs)."),
    ("RESULTS", "20", "Results of syntheses."),
    ("RESULTS", "21", "Reporting biases results."),
    ("RESULTS", "22", "Certainty of evidence results."),
    ("DISCUSSION", "23", "Interpretation, limitations, implications."),
    ("OTHER", "24", "Registration and protocol information."),
    ("OTHER", "25", "Support/funding and role of funders."),
    ("OTHER", "26", "Competing interests."),
    ("OTHER", "27", "Availability of data, code and other materials."),
]

# Risk-of-bias tools and their assessment domains.
ROB_TOOLS = {
    "RoB2 (randomized trials)": [
        "randomization_process",
        "deviations_from_intended_interventions",
        "missing_outcome_data",
        "measurement_of_outcome",
        "selection_of_reported_result",
        "overall",
    ],
    "ROBINS-I (non-randomized)": [
        "confounding",
        "selection_of_participants",
        "classification_of_interventions",
        "deviations_from_interventions",
        "missing_data",
        "measurement_of_outcomes",
        "selection_of_reported_result",
        "overall",
    ],
    "AMSTAR2 (systematic reviews)": [f"item_{i}" for i in range(1, 17)] + ["overall_confidence"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def _hash_config(config_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    if config_root and config_root.exists():
        for path in sorted(config_root.glob("*.json")):
            hashes[path.name] = _sha256(path)
    return hashes


def build_prisma2020_rows(provider_rows: dict, summary: dict) -> list[dict]:
    """One row per database with identified records, plus aggregate screening."""
    rows: list[dict] = []
    for provider, count in sorted(provider_rows.items()):
        rows.append({"stage": "identified", "source": provider, "n_records": int(count or 0)})
    rows.append({"stage": "identified_total", "source": "all_databases", "n_records": int(summary.get("records", 0))})
    rows.append({"stage": "duplicates_removed", "source": "all_databases", "n_records": int(summary.get("duplicate_rows", 0))})
    rows.append({"stage": "screened_unique_documents", "source": "all_databases", "n_records": int(summary.get("curated_unique_documents", 0))})
    rows.append({"stage": "full_text_retrieved", "source": "all_databases", "n_records": int(summary.get("downloads_ok", 0))})
    rows.append({"stage": "evidence_claims_extracted", "source": "all_databases", "n_records": int(summary.get("evidence_claims_total", 0))})
    rows.append({"stage": "recommendation_candidates", "source": "all_databases", "n_records": int(summary.get("recommendation_candidates_total", 0))})
    return rows


def render_search_appendix(provider_querypack: dict, provider_rows: dict, search_date: str) -> str:
    lines = [
        "# Search strategy appendix (per database)",
        "",
        f"Search executed/exported on: {search_date}",
        "",
        "Each block lists the exact queries submitted to a database for a given",
        "workstream, so the search is fully reproducible (PRISMA 2020, item 7).",
        "",
    ]
    for workstream in sorted(provider_querypack):
        providers = provider_querypack[workstream]
        if not providers:
            continue
        lines.append(f"## Workstream: {workstream}")
        lines.append("")
        for provider in sorted(providers):
            queries = providers[provider] or []
            lines.append(f"### {provider} — {len(queries)} query(ies); {int(provider_rows.get(provider, 0))} record(s) retrieved (all workstreams)")
            lines.append("")
            for i, query in enumerate(queries, start=1):
                lines.append(f"{i}. `{query}`")
            lines.append("")
    return "\n".join(lines)


def render_prospero_template(summary: dict, databases: list[str], search_date: str) -> str:
    return "\n".join(
        [
            "# PROSPERO protocol registration template (NutEV/NutMEV)",
            "",
            "> Fill and register BEFORE screening/extraction. Registration is",
            "> required/expected by QUALIS A1 journals (PRISMA 2020, item 24).",
            "",
            "- **Review title**: ",
            "- **Anticipated/actual start date**: ",
            f"- **Date of this draft**: {search_date}",
            "- **Review question (PICO/PECO)**: ",
            "  - Population: ",
            "  - Intervention/Exposure: ",
            "  - Comparator: ",
            "  - Outcomes: ",
            "- **Searches**: ",
            f"  - Databases searched: {', '.join(databases)}",
            "  - Date(s) of search: " + search_date,
            "  - Search strategy: see NUTEV_SEARCH_STRATEGY_APPENDIX.md (verbatim per database).",
            "  - Language/date limits: ",
            "- **Condition or domain being studied**: lifestyle nutrition / cardiometabolic-kidney-metabolic health.",
            "- **Eligibility criteria (inclusion/exclusion)**: ",
            "- **Study designs included**: ",
            "- **Data extraction (selection & coding)**: dual independent screening; NutEV provides candidate claims only.",
            "- **Risk of bias assessment**: RoB 2 / ROBINS-I / AMSTAR 2 (see NUTEV_RISK_OF_BIAS.csv).",
            "- **Strategy for data synthesis**: ",
            "- **Certainty of evidence**: GRADE.",
            "- **Conflicts of interest / funding**: ",
            "",
            "_NutEV note: RecommendationCandidate outputs are not final protocol",
            "recommendations and require human review, documentary anchoring and",
            "methodological adjudication._",
        ]
    )


def render_prisma_checklist() -> str:
    lines = [
        "# PRISMA 2020 checklist",
        "",
        "Reference: Page MJ, et al. BMJ 2021;372:n71. Fill 'Location/Status' per item.",
        "",
        "| Section | Item | Recommendation | Location/Status |",
        "| --- | --- | --- | --- |",
    ]
    for section, item, desc in PRISMA_2020_ITEMS:
        lines.append(f"| {section} | {item} | {desc} | _to complete_ |")
    return "\n".join(lines)


def build_risk_of_bias_rows(included_documents: list[dict] | None) -> list[dict]:
    docs = included_documents or []
    columns_help = {tool: "|".join(domains) for tool, domains in ROB_TOOLS.items()}
    rows: list[dict] = []
    for doc in docs:
        base = {
            "document_id": str(doc.get("document_id", "")),
            "title": str(doc.get("title", "")),
            "year": str(doc.get("year", "")),
            "study_design": str(doc.get("article_type", "") or doc.get("evidence_type", "")),
            "assessment_tool": "",
        }
        for tool, domains in ROB_TOOLS.items():
            for domain in domains:
                base[f"{tool.split(' ')[0]}::{domain}"] = ""
        rows.append(base)
    if not rows:
        # Always emit a header-only template (with tool guidance) for an empty run.
        placeholder = {"document_id": "", "title": "", "year": "", "study_design": "", "assessment_tool": ""}
        for tool, domains in ROB_TOOLS.items():
            for domain in domains:
                placeholder[f"{tool.split(' ')[0]}::{domain}"] = ""
        rows.append(placeholder)
    return rows, columns_help


def build_reproducibility_report(
    *,
    provider_rows: dict,
    provider_querypack: dict,
    summary: dict,
    config_root: Path,
    package_version: str,
    started_at: str,
    finished_at: str,
) -> dict:
    total_queries = sum(len(qs or []) for ws in provider_querypack.values() for qs in ws.values())
    return {
        "generated_at": _now(),
        "tool": "NutEV/NutMEV",
        "package_version": package_version,
        "run_started_at": started_at,
        "run_finished_at": finished_at,
        "databases": sorted(provider_rows.keys()),
        "records_by_database": {k: int(v or 0) for k, v in sorted(provider_rows.items())},
        "total_queries_executed": int(total_queries),
        "records_total": int(summary.get("records", 0)),
        "unique_documents": int(summary.get("curated_unique_documents", 0)),
        "downloads_ok": int(summary.get("downloads_ok", 0)),
        "evidence_claims_total": int(summary.get("evidence_claims_total", 0)),
        "recommendation_candidates_total": int(summary.get("recommendation_candidates_total", 0)),
        "config_sha256": _hash_config(config_root),
        "reproducibility_note": (
            "Re-running with the same package version, configuration hashes and "
            "search strategy reproduces the deterministic identification/curation "
            "stages; live database results may change as sources are updated."
        ),
    }


def write_qualis_methods(
    *,
    tables_dir: Path,
    docs_dir: Path,
    provider_rows: dict,
    provider_querypack: dict,
    summary: dict,
    config_root: Path,
    package_version: str,
    started_at: str = "",
    finished_at: str = "",
    included_documents: list[dict] | None = None,
) -> dict:
    tables_dir = Path(tables_dir)
    docs_dir = Path(docs_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    search_date = (finished_at or _now())[:10]
    databases = sorted(provider_rows.keys())

    prisma_rows = build_prisma2020_rows(provider_rows, summary)
    write_simple_csv(prisma_rows, tables_dir / "NUTEV_PRISMA2020_FLOW.csv", fieldnames=["stage", "source", "n_records"])

    write_text(docs_dir / "NUTEV_SEARCH_STRATEGY_APPENDIX.md", render_search_appendix(provider_querypack, provider_rows, search_date))
    write_text(docs_dir / "NUTEV_PROSPERO_PROTOCOL.md", render_prospero_template(summary, databases, search_date))
    write_text(docs_dir / "NUTEV_PRISMA2020_CHECKLIST.md", render_prisma_checklist())

    rob_rows, rob_help = build_risk_of_bias_rows(included_documents)
    write_simple_csv(rob_rows, tables_dir / "NUTEV_RISK_OF_BIAS.csv", fieldnames=list(rob_rows[0].keys()))
    write_text(
        docs_dir / "NUTEV_RISK_OF_BIAS_GUIDE.md",
        "# Risk of bias — tool/domain guide\n\n"
        + "\n".join(f"- **{tool}**: {domains}" for tool, domains in rob_help.items())
        + "\n\nAssess each included study with the tool matching its design; "
        "record per-domain judgements (low / some concerns / high) in NUTEV_RISK_OF_BIAS.csv.",
    )

    report = build_reproducibility_report(
        provider_rows=provider_rows,
        provider_querypack=provider_querypack,
        summary=summary,
        config_root=config_root,
        package_version=package_version,
        started_at=started_at,
        finished_at=finished_at,
    )
    (tables_dir / "NUTEV_REPRODUCIBILITY.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "prisma2020_rows": len(prisma_rows),
        "databases": databases,
        "total_queries_executed": report["total_queries_executed"],
        "risk_of_bias_rows": len(rob_rows),
        "qualis_artifacts": [
            "06_tables/NUTEV_PRISMA2020_FLOW.csv",
            "06_tables/NUTEV_RISK_OF_BIAS.csv",
            "06_tables/NUTEV_REPRODUCIBILITY.json",
            "08_docs/NUTEV_SEARCH_STRATEGY_APPENDIX.md",
            "08_docs/NUTEV_PROSPERO_PROTOCOL.md",
            "08_docs/NUTEV_PRISMA2020_CHECKLIST.md",
            "08_docs/NUTEV_RISK_OF_BIAS_GUIDE.md",
        ],
    }
