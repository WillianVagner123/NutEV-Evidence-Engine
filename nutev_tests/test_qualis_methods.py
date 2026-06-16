from __future__ import annotations

import csv
import json
from pathlib import Path

from nutev.export.qualis_methods import (
    PRISMA_2020_ITEMS,
    build_prisma2020_rows,
    write_qualis_methods,
)


def _csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_prisma2020_has_per_database_identified_rows() -> None:
    provider_rows = {"pubmed": 10, "scielo": 4}
    summary = {"records": 14, "duplicate_rows": 2, "curated_unique_documents": 12}
    rows = build_prisma2020_rows(provider_rows, summary)
    identified = {r["source"]: r["n_records"] for r in rows if r["stage"] == "identified"}
    assert identified == {"pubmed": 10, "scielo": 4}
    stages = {r["stage"] for r in rows}
    assert {"identified_total", "duplicates_removed", "screened_unique_documents"} <= stages


def test_prisma_checklist_has_27_items() -> None:
    assert len(PRISMA_2020_ITEMS) == 27


def test_write_qualis_methods_creates_all_artifacts(tmp_path: Path) -> None:
    tables = tmp_path / "06_tables"
    docs = tmp_path / "08_docs"
    config = tmp_path / "config"
    config.mkdir()
    (config / "keyword_taxonomy.json").write_text('{"a": 1}', encoding="utf-8")

    provider_rows = {"pubmed": 5, "semantic_scholar": 3, "scielo": 2}
    provider_querypack = {"busca2b": {"pubmed": ['"diet"[Title/Abstract]'], "scielo": ['("diet")']}}
    summary = {"records": 10, "duplicate_rows": 1, "curated_unique_documents": 9, "downloads_ok": 4, "evidence_claims_total": 7, "recommendation_candidates_total": 2}
    included = [{"document_id": "doc_1", "title": "Trial", "year": 2025, "article_type": "RCT", "download_status": "pdf"}]

    out = write_qualis_methods(
        tables_dir=tables,
        docs_dir=docs,
        provider_rows=provider_rows,
        provider_querypack=provider_querypack,
        summary=summary,
        config_root=config,
        package_version="9.9.9",
        finished_at="2026-06-15T00:00:00+00:00",
        included_documents=included,
    )

    for rel in out["qualis_artifacts"]:
        name = rel.split("/", 1)[1]
        folder = tables if rel.startswith("06_tables") else docs
        assert (folder / name).exists(), f"missing {rel}"

    # PRISMA flow has the per-database identified rows
    prisma = _csv_rows(tables / "NUTEV_PRISMA2020_FLOW.csv")
    assert any(r["source"] == "semantic_scholar" and r["stage"] == "identified" for r in prisma)

    # Search appendix contains the verbatim query
    appendix = (docs / "NUTEV_SEARCH_STRATEGY_APPENDIX.md").read_text(encoding="utf-8")
    assert '"diet"[Title/Abstract]' in appendix
    assert "busca2b" in appendix

    # Reproducibility report hashes the config and records versions/queries
    report = json.loads((tables / "NUTEV_REPRODUCIBILITY.json").read_text(encoding="utf-8"))
    assert report["package_version"] == "9.9.9"
    assert report["total_queries_executed"] == 2
    assert "keyword_taxonomy.json" in report["config_sha256"]
    assert len(report["config_sha256"]["keyword_taxonomy.json"]) == 64  # sha256 hex

    # Risk-of-bias template has one row per included document with tool domains
    rob = _csv_rows(tables / "NUTEV_RISK_OF_BIAS.csv")
    assert len(rob) == 1
    assert rob[0]["document_id"] == "doc_1"
    assert any(col.startswith("RoB2::") for col in rob[0])

    # Checklist + PROSPERO present with content
    assert "PRISMA 2020 checklist" in (docs / "NUTEV_PRISMA2020_CHECKLIST.md").read_text(encoding="utf-8")
    assert "PROSPERO" in (docs / "NUTEV_PROSPERO_PROTOCOL.md").read_text(encoding="utf-8")
