from __future__ import annotations

from pathlib import Path

import pandas as pd

from nutev.engine.identity import (
    as_text,
    compute_document_key,
    has_full_text,
    normalize_doi,
    normalize_for_match,
    normalize_title,
    normalize_url,
    normalize_year,
)
from nutev.export.excel_writer import (
    sanitize_dataframe_for_excel,
    write_excel_file,
    write_excel_sheet,
)
from nutev.export.metadata_tables import REQUIRED_METADATA_COLUMNS

CURATED_METADATA_COLUMNS = REQUIRED_METADATA_COLUMNS + [
    "document_key",
    "document_key_type",
    "doi_normalized",
    "url_normalized",
    "title_normalized",
    "year_normalized",
    "workstream_list",
    "has_full_text",
    "is_metadata_only",
    "is_prioritized",
]

UNIQUE_DOCUMENT_COLUMNS = [
    "document_key",
    "document_key_type",
    "title",
    "year",
    "doi",
    "pmid",
    "pmcid",
    "original_url",
    "final_url",
    "source_provider",
    "evidence_type",
    "download_status",
    "capture_status",
    "extraction_status",
    "workstreams",
    "document_ids",
    "source_occurrences",
    "has_full_text",
    "is_metadata_only",
    "is_prioritized",
]

WORKSTREAM_MAP_COLUMNS = [
    "document_key",
    "document_id",
    "workstream",
    "source_provider",
    "title",
    "year",
    "download_status",
    "extraction_status",
    "is_prioritized",
]

PRISMA_COLUMNS = [
    "registros_identificados",
    "duplicados_removidos",
    "registros_triados",
    "documentos_com_pdf_ou_html",
    "documentos_metadata_only",
    "documentos_priorizados",
]

PRISMA_NOTE_COLUMNS = ["nota"]
QA_SUMMARY_COLUMNS = ["metric", "value"]
DUPLICATE_SUMMARY_COLUMNS = [
    "document_key_type",
    "duplicate_documents",
    "duplicate_rows",
]
MISSING_BY_WORKSTREAM_COLUMNS = [
    "workstream",
    "missing_title",
    "missing_url",
    "missing_year",
    "missing_evidence_type",
]

_PRIORITY_TERMS = [
    "obesity",
    "obesidade",
    "overweight",
    "sobrepeso",
    "adiposity",
    "adiposidade",
    "cardiometabolic",
    "cardiometabolic risk",
    "risco cardiometabolico",
    "risco cardiometabólico",
    "diabetes",
    "type 2 diabetes",
    "diabetes tipo 2",
    "hypertension",
    "hipertensao",
    "hipertensão",
    "dyslipidemia",
    "dislipidemia",
    "masld",
    "nafld",
    "esteatose hepatica",
    "esteatose hepática",
    "mediterranean",
    "dieta mediterranea",
    "dieta mediterrânea",
    "dash",
    "mind",
    "plant-based",
    "plant based",
    "eat-lancet",
    "planetary health diet",
    "dietary guideline",
    "dietary guidelines",
    "food-based dietary guideline",
    "food-based dietary guidelines",
    "lifestyle medicine",
    "medicina do estilo de vida",
    "culinary medicine",
    "medicina culinaria",
    "medicina culinária",
    "food literacy",
    "literacia alimentar",
    "adherence",
    "adesao",
    "adesão",
    "implementation",
    "implementacao",
    "implementação",
    "barrier",
    "barriers",
    "facilitator",
    "facilitators",
    "commensality",
    "comensalidade",
    "meal planning",
    "planejamento alimentar",
    "behavior change",
    "behaviour change",
    "mudanca de comportamento",
    "mudança de comportamento",
    "self-efficacy",
    "autoeficacia",
    "autoeficácia",
]


def _compute_document_key(row: dict) -> tuple[str, str]:
    return compute_document_key(row)


def _has_full_text(row: dict) -> bool:
    return has_full_text(row)


def _is_prioritized(row: dict) -> bool:
    try:
        score = float(row.get("relevance_score") or row.get("score") or 0)
    except Exception:
        score = 0.0
    text = " ".join(
        [
            as_text(row.get("title")),
            as_text(row.get("evidence_type")),
            as_text(row.get("domains")),
            as_text(row.get("outcomes")),
            as_text(row.get("diet_patterns")),
            as_text(row.get("clinical_conditions")),
            as_text(row.get("main_terms")),
        ]
    )
    normalized_text = normalize_for_match(text)
    return score >= 8 and any(
        normalize_for_match(term) in normalized_text for term in _PRIORITY_TERMS
    )


def _curate_row(row: dict) -> dict:
    curated = {
        column: as_text(row.get(column)) for column in REQUIRED_METADATA_COLUMNS
    }
    curated["document_id"] = as_text(row.get("document_id") or row.get("id"))
    curated["title"] = as_text(row.get("title"))
    curated["doi"] = as_text(row.get("doi"))
    curated["pmid"] = as_text(row.get("pmid"))
    curated["pmcid"] = as_text(row.get("pmcid"))
    curated["original_url"] = as_text(row.get("original_url") or row.get("url"))
    curated["final_url"] = as_text(
        row.get("final_url") or row.get("resolved_url") or row.get("url")
    )
    curated["artifact_paths"] = as_text(
        row.get("artifact_paths") or row.get("file_path")
    )
    curated["source_provider"] = as_text(
        row.get("source_provider") or row.get("source")
    )
    curated["workstream"] = as_text(row.get("workstream"))
    curated["capture_status"] = as_text(row.get("capture_status") or "missing")
    curated["download_status"] = as_text(
        row.get("download_status")
        or ("pdf" if row.get("file_path") else "metadata_only")
    )
    curated["extraction_status"] = as_text(
        row.get("extraction_status") or "missing"
    )
    curated["relevance_score"] = row.get("relevance_score") or row.get("score") or ""
    curated["novelty_score"] = row.get("novelty_score") or ""
    curated["domains"] = as_text(row.get("domains"))
    curated["outcomes"] = as_text(row.get("outcomes"))
    curated["diet_patterns"] = as_text(
        row.get("diet_patterns") or row.get("diet_pattern")
    )
    curated["clinical_conditions"] = as_text(
        row.get("clinical_conditions") or row.get("clinical_condition")
    )

    document_key, document_key_type = _compute_document_key(curated)
    curated["document_key"] = document_key
    curated["document_key_type"] = document_key_type
    curated["doi_normalized"] = normalize_doi(curated.get("doi"))
    curated["url_normalized"] = normalize_url(
        curated.get("final_url") or curated.get("original_url")
    )
    curated["title_normalized"] = normalize_title(curated.get("title"))
    curated["year_normalized"] = normalize_year(curated.get("year"))
    curated["workstream_list"] = curated.get("workstream", "")
    curated["has_full_text"] = _has_full_text(curated)
    curated["is_metadata_only"] = not curated["has_full_text"]
    curated["is_prioritized"] = _is_prioritized(curated)
    return curated


def _rank_row(row: dict) -> tuple[int, int, float, int, str]:
    try:
        score = float(row.get("relevance_score") or 0)
    except Exception:
        score = 0.0
    try:
        year = int(row.get("year_normalized") or 0)
    except Exception:
        year = 0
    return (
        int(bool(row.get("has_full_text"))),
        int(bool(row.get("is_prioritized"))),
        score,
        year,
        as_text(row.get("title")),
    )


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def _build_unique_documents(curated_rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in curated_rows:
        grouped.setdefault(row["document_key"], []).append(row)

    unique_rows = []
    for document_key in sorted(grouped):
        group = sorted(grouped[document_key], key=_rank_row, reverse=True)
        best = dict(group[0])
        workstreams = sorted(
            {
                as_text(item.get("workstream"))
                for item in group
                if as_text(item.get("workstream"))
            }
        )
        document_ids = sorted(
            {
                as_text(item.get("document_id"))
                for item in group
                if as_text(item.get("document_id"))
            }
        )
        best.update(
            {
                "workstreams": "; ".join(workstreams),
                "document_ids": "; ".join(document_ids),
                "source_occurrences": len(group),
                "has_full_text": any(
                    bool(item.get("has_full_text")) for item in group
                ),
                "is_metadata_only": not any(
                    bool(item.get("has_full_text")) for item in group
                ),
                "is_prioritized": any(
                    bool(item.get("is_prioritized")) for item in group
                ),
            }
        )
        unique_rows.append(
            {column: best.get(column, "") for column in UNIQUE_DOCUMENT_COLUMNS}
        )
    return unique_rows


def _build_workstream_map(curated_rows: list[dict]) -> list[dict]:
    selected: dict[tuple[str, str], dict] = {}
    for row in sorted(curated_rows, key=_rank_row, reverse=True):
        workstream = as_text(row.get("workstream")) or "unassigned"
        key = (row["document_key"], workstream)
        selected.setdefault(key, row)
    return [
        {
            column: row.get(
                column if column != "workstream" else "workstream", ""
            )
            for column in WORKSTREAM_MAP_COLUMNS
        }
        for _, row in sorted(selected.items())
    ]


def _build_duplicate_rows(curated_rows: list[dict]) -> pd.DataFrame:
    counts: dict[str, int] = {}
    for row in curated_rows:
        counts[row["document_key"]] = counts.get(row["document_key"], 0) + 1
    duplicates = []
    for row in curated_rows:
        occurrences = counts[row["document_key"]]
        if occurrences > 1:
            duplicates.append(
                {
                    "document_key": row["document_key"],
                    "document_key_type": row["document_key_type"],
                    "document_id": row.get("document_id", ""),
                    "title": row.get("title", ""),
                    "workstream": row.get("workstream", ""),
                    "occurrences": occurrences,
                }
            )
    return pd.DataFrame(
        duplicates,
        columns=[
            "document_key",
            "document_key_type",
            "document_id",
            "title",
            "workstream",
            "occurrences",
        ],
    )


def _build_duplicate_summary(curated_rows: list[dict]) -> pd.DataFrame:
    grouped: dict[str, dict[str, int]] = {}
    key_counts: dict[str, int] = {}
    key_types: dict[str, str] = {}
    for row in curated_rows:
        key = row["document_key"]
        key_counts[key] = key_counts.get(key, 0) + 1
        key_types[key] = row["document_key_type"]
    for key, count in key_counts.items():
        if count <= 1:
            continue
        key_type = key_types[key]
        bucket = grouped.setdefault(
            key_type, {"duplicate_documents": 0, "duplicate_rows": 0}
        )
        bucket["duplicate_documents"] += 1
        bucket["duplicate_rows"] += count - 1
    rows = [
        {
            "document_key_type": key_type,
            "duplicate_documents": values["duplicate_documents"],
            "duplicate_rows": values["duplicate_rows"],
        }
        for key_type, values in sorted(grouped.items())
    ]
    return pd.DataFrame(rows, columns=DUPLICATE_SUMMARY_COLUMNS)


def _build_missing_canonical_rows(curated_rows: list[dict]) -> pd.DataFrame:
    rows = []
    for row in curated_rows:
        missing = []
        if not as_text(row.get("title")):
            missing.append("title")
        if not as_text(row.get("final_url") or row.get("original_url")):
            missing.append("url")
        if not as_text(row.get("year")):
            missing.append("year")
        if not as_text(row.get("evidence_type")):
            missing.append("evidence_type")
        if missing:
            rows.append(
                {
                    "document_key": row.get("document_key", ""),
                    "document_id": row.get("document_id", ""),
                    "title": row.get("title", ""),
                    "workstream": row.get("workstream", ""),
                    "missing_fields": "; ".join(missing),
                }
            )
    return pd.DataFrame(
        rows,
        columns=[
            "document_key",
            "document_id",
            "title",
            "workstream",
            "missing_fields",
        ],
    )


def _build_missing_by_workstream(curated_rows: list[dict]) -> pd.DataFrame:
    grouped: dict[str, dict[str, int]] = {}
    for row in curated_rows:
        workstream = as_text(row.get("workstream")) or "unassigned"
        bucket = grouped.setdefault(
            workstream,
            {
                "missing_title": 0,
                "missing_url": 0,
                "missing_year": 0,
                "missing_evidence_type": 0,
            },
        )
        if not as_text(row.get("title")):
            bucket["missing_title"] += 1
        if not as_text(row.get("final_url") or row.get("original_url")):
            bucket["missing_url"] += 1
        if not as_text(row.get("year")):
            bucket["missing_year"] += 1
        if not as_text(row.get("evidence_type")):
            bucket["missing_evidence_type"] += 1
    rows = [
        {"workstream": workstream, **values}
        for workstream, values in sorted(grouped.items())
    ]
    return pd.DataFrame(rows, columns=MISSING_BY_WORKSTREAM_COLUMNS)


def _build_status_counts(curated_rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(curated_rows)
    if df.empty:
        return pd.DataFrame(columns=["download_status", "extraction_status", "n"])
    return (
        df.groupby(["download_status", "extraction_status"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(
            ["n", "download_status", "extraction_status"],
            ascending=[False, True, True],
        )
    )


def _build_workstream_counts(curated_rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(curated_rows)
    if df.empty:
        return pd.DataFrame(columns=["workstream", "n"])
    return df.groupby("workstream", dropna=False).size().reset_index(
        name="n"
    ).sort_values(["n", "workstream"], ascending=[False, True])


def _build_qa_summary(
    curated_rows: list[dict], unique_rows: list[dict], workstream_map: list[dict]
) -> pd.DataFrame:
    duplicate_rows = max(0, len(curated_rows) - len(unique_rows))
    metadata_only_docs = sum(1 for row in unique_rows if row.get("is_metadata_only"))
    unique_count = len(unique_rows)
    metadata_only_share = round(
        (metadata_only_docs / unique_count) * 100, 2
    ) if unique_count else 0.0
    summary = [
        {"metric": "raw_records", "value": len(curated_rows)},
        {"metric": "unique_documents", "value": unique_count},
        {"metric": "document_workstream_pairs", "value": len(workstream_map)},
        {"metric": "duplicate_rows_removed", "value": duplicate_rows},
        {
            "metric": "documents_with_full_text",
            "value": sum(1 for row in unique_rows if row.get("has_full_text")),
        },
        {
            "metric": "documents_metadata_only",
            "value": metadata_only_docs,
        },
        {
            "metric": "documents_metadata_only_pct",
            "value": metadata_only_share,
        },
        {
            "metric": "documents_prioritized",
            "value": sum(1 for row in unique_rows if row.get("is_prioritized")),
        },
        {
            "metric": "missing_title",
            "value": sum(
                1 for row in curated_rows if not as_text(row.get("title"))
            ),
        },
        {
            "metric": "missing_url",
            "value": sum(
                1
                for row in curated_rows
                if not as_text(row.get("final_url") or row.get("original_url"))
            ),
        },
        {
            "metric": "missing_year",
            "value": sum(1 for row in curated_rows if not as_text(row.get("year"))),
        },
        {
            "metric": "missing_evidence_type",
            "value": sum(
                1
                for row in curated_rows
                if not as_text(row.get("evidence_type"))
            ),
        },
    ]
    return pd.DataFrame(summary, columns=QA_SUMMARY_COLUMNS)


def _build_prisma_corrected(
    curated_rows: list[dict], unique_rows: list[dict]
) -> pd.DataFrame:
    flow = {
        "registros_identificados": len(curated_rows),
        "duplicados_removidos": max(0, len(curated_rows) - len(unique_rows)),
        "registros_triados": len(unique_rows),
        "documentos_com_pdf_ou_html": sum(
            1 for row in unique_rows if row.get("has_full_text")
        ),
        "documentos_metadata_only": sum(
            1 for row in unique_rows if row.get("is_metadata_only")
        ),
        "documentos_priorizados": sum(
            1 for row in unique_rows if row.get("is_prioritized")
        ),
    }
    return pd.DataFrame([flow], columns=PRISMA_COLUMNS)


def curate_outputs(rows: list[dict], curated_dir: Path) -> dict[str, int]:
    curated_dir.mkdir(parents=True, exist_ok=True)

    curated_rows = [_curate_row(row) for row in rows]
    curated_df = pd.DataFrame(curated_rows, columns=CURATED_METADATA_COLUMNS)
    unique_rows = _build_unique_documents(curated_rows)
    unique_df = pd.DataFrame(unique_rows, columns=UNIQUE_DOCUMENT_COLUMNS)
    workstream_map = _build_workstream_map(curated_rows)
    workstream_df = pd.DataFrame(workstream_map, columns=WORKSTREAM_MAP_COLUMNS)
    duplicate_df = _build_duplicate_rows(curated_rows)
    duplicate_summary_df = _build_duplicate_summary(curated_rows)
    missing_df = _build_missing_canonical_rows(curated_rows)
    missing_by_workstream_df = _build_missing_by_workstream(curated_rows)
    status_df = _build_status_counts(curated_rows)
    workstream_counts_df = _build_workstream_counts(curated_rows)
    qa_summary_df = _build_qa_summary(curated_rows, unique_rows, workstream_map)
    prisma_df = _build_prisma_corrected(curated_rows, unique_rows)
    prisma_notes_df = pd.DataFrame(
        [
            {
                "nota": (
                    "PRISMA operacional corrigido: registros_identificados = "
                    "linhas brutas; duplicados_removidos = linhas brutas - "
                    "documentos únicos; registros_triados = documentos únicos."
                )
            }
        ],
        columns=PRISMA_NOTE_COLUMNS,
    )

    _write_csv(curated_df, curated_dir / "NUTEV_METADATA_CURATED.csv")
    write_excel_file(
        sanitize_dataframe_for_excel(curated_df),
        curated_dir / "NUTEV_METADATA_CURATED.xlsx",
    )

    _write_csv(unique_df, curated_dir / "NUTEV_DOCUMENTS_UNIQUE.csv")
    write_excel_file(
        sanitize_dataframe_for_excel(unique_df),
        curated_dir / "NUTEV_DOCUMENTS_UNIQUE.xlsx",
    )

    _write_csv(workstream_df, curated_dir / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv")

    with pd.ExcelWriter(curated_dir / "NUTEV_QA_REPORT.xlsx") as writer:
        write_excel_sheet(writer, qa_summary_df, "summary")
        write_excel_sheet(writer, duplicate_df, "duplicate_keys")
        write_excel_sheet(writer, duplicate_summary_df, "duplicate_summary")
        write_excel_sheet(writer, missing_df, "missing_canonical")
        write_excel_sheet(writer, missing_by_workstream_df, "missing_by_workstream")
        write_excel_sheet(writer, status_df, "status_counts")
        write_excel_sheet(writer, workstream_counts_df, "workstream_counts")

    with pd.ExcelWriter(curated_dir / "NUTEV_PRISMA_FLOW_CORRIGIDO.xlsx") as writer:
        write_excel_sheet(writer, prisma_df, "flow")
        write_excel_sheet(writer, prisma_notes_df, "notes")

    return {
        "raw_records": len(curated_rows),
        "unique_documents": len(unique_rows),
        "document_workstream_pairs": len(workstream_map),
    }
