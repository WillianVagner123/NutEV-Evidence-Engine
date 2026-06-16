"""Build an AI-/RAG-ready knowledge base from the consolidated article rows.

Produces one clean record per de-duplicated document in three formats:
- ``corpus.jsonl`` — rich, list fields preserved; the source for retrieval/RAG.
- ``corpus.csv``   — universal tabular access (list fields ``;``-joined).
- ``corpus.parquet`` — efficient columnar access for pandas/BI (best-effort).
Plus ``data_dictionary.md`` and ``schema.json`` so a human or an LLM knows the
field semantics before querying the base.
"""

from __future__ import annotations

import ast
import csv
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Field name -> (type, human/AI-readable description). Drives the data dictionary
# and the corpus schema, and defines the canonical column order.
KB_FIELDS: list[tuple[str, str, str]] = [
    ("document_id", "str", "Stable identifier for the de-duplicated document."),
    ("workstream", "str", "Search workstream that surfaced the document."),
    ("title", "str", "Document title (original language)."),
    ("abstract", "str", "Abstract / summary text."),
    ("authors", "str", "Author names, '; '-separated."),
    ("year", "int", "Publication year (null if unknown)."),
    ("language", "str", "ISO-639-1 language code (provider-reported or detected)."),
    ("countries", "list[str]", "ISO-3166 alpha-2 codes of author-institution countries."),
    ("region", "str", "Continent/region of the primary country."),
    ("journal", "str", "Journal / venue name."),
    ("issn", "str", "Journal ISSN (linking ISSN when available)."),
    ("publisher", "str", "Publisher / host organization."),
    ("doi", "str", "Digital Object Identifier."),
    ("url", "str", "Best access URL (full text when available)."),
    ("source_providers", "list[str]", "Providers that returned this record."),
    ("domains", "list[str]", "Evidence domains matched by the classifier."),
    ("outcomes", "list[str]", "Health outcomes matched by the classifier."),
    ("diet_patterns", "list[str]", "Dietary patterns inferred from the text."),
    ("clinical_conditions", "list[str]", "Clinical conditions inferred from the text."),
    ("evidence_type", "str", "Evidence/article type (e.g. systematic_review, trial)."),
    ("evidence_tier", "str", "Editorial/evidence priority tier."),
    ("relevance_score", "number", "Rule-based relevance score."),
    ("cited_by_count", "int", "Citation count (when reported by the source)."),
]

_LIST_FIELDS = {name for name, typ, _ in KB_FIELDS if typ.startswith("list")}
_FIELD_ORDER = [name for name, _, _ in KB_FIELDS]
_SPLIT_RE = re.compile(r"\s*;\s*|\s*,\s*")


def _coerce_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text[0] == "[" and text[-1] == "]":
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, (list, tuple)):
                    return [str(v).strip() for v in parsed if str(v).strip()]
            except (ValueError, SyntaxError):
                pass
        return [p.strip() for p in _SPLIT_RE.split(text) if p.strip()]
    return []


def _coerce_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            return int(match.group())
    return None


def _document_id(row: dict) -> str:
    for key in ("document_id", "id", "doi", "pmid", "pmcid"):
        val = str(row.get(key) or "").strip()
        if val:
            return val
    return str(row.get("final_url") or row.get("url") or row.get("title") or "").strip()


def to_kb_record(row: dict) -> dict:
    providers = _coerce_list(row.get("source_providers") or row.get("matched_providers"))
    if not providers:
        single = str(row.get("source_provider") or row.get("source") or "").strip()
        providers = [single] if single else []
    return {
        "document_id": _document_id(row),
        "workstream": str(row.get("workstream") or ""),
        "title": str(row.get("title") or ""),
        "abstract": str(row.get("abstract") or row.get("snippet") or ""),
        "authors": str(row.get("authors") or ""),
        "year": _coerce_int(row.get("year")),
        "language": str(row.get("language") or ""),
        "countries": _coerce_list(row.get("countries")),
        "region": str(row.get("region") or ""),
        "journal": str(row.get("journal") or ""),
        "issn": str(row.get("issn") or ""),
        "publisher": str(row.get("publisher") or ""),
        "doi": str(row.get("doi") or ""),
        "url": str(row.get("final_url") or row.get("url") or ""),
        "source_providers": providers,
        "domains": _coerce_list(row.get("domains")),
        "outcomes": _coerce_list(row.get("outcomes")),
        "diet_patterns": _coerce_list(row.get("diet_patterns")),
        "clinical_conditions": _coerce_list(row.get("clinical_conditions")),
        "evidence_type": str(row.get("evidence_type") or row.get("article_type") or ""),
        "evidence_tier": str(row.get("editorial_priority_tier") or row.get("evidence_priority_tier") or ""),
        "relevance_score": row.get("relevance_score") or 0,
        "cited_by_count": _coerce_int(row.get("cited_by_count")) or 0,
    }


def to_kb_records(rows: list[dict]) -> list[dict]:
    records = [to_kb_record(r) for r in rows if isinstance(r, dict)]
    return [r for r in records if r["document_id"]]


def _flat(value: object) -> object:
    if isinstance(value, list):
        return ";".join(str(v) for v in value)
    return value


def write_knowledge_base(records: list[dict], kb_dir: Path) -> dict[str, Path]:
    kb_dir = Path(kb_dir)
    kb_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    corpus_jsonl = kb_dir / "corpus.jsonl"
    with corpus_jsonl.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    paths["corpus_jsonl"] = corpus_jsonl

    corpus_csv = kb_dir / "corpus.csv"
    with corpus_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELD_ORDER)
        writer.writeheader()
        for record in records:
            writer.writerow({k: _flat(record.get(k, "")) for k in _FIELD_ORDER})
    paths["corpus_csv"] = corpus_csv

    try:
        import pandas as pd

        frame = pd.DataFrame([{k: _flat(r.get(k, "")) for k in _FIELD_ORDER} for r in records], columns=_FIELD_ORDER)
        corpus_parquet = kb_dir / "corpus.parquet"
        frame.to_parquet(corpus_parquet, index=False)
        paths["corpus_parquet"] = corpus_parquet
    except Exception as exc:  # pragma: no cover - parquet engine optional
        logger.warning("knowledge base parquet skipped: %s", exc)

    schema_path = kb_dir / "schema.json"
    schema_path.write_text(
        json.dumps(
            {"fields": [{"name": n, "type": t, "description": d} for n, t, d in KB_FIELDS]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    paths["schema"] = schema_path

    dictionary = ["# Knowledge base data dictionary", "", f"Records: {len(records)} (one per de-duplicated document).", ""]
    dictionary += ["| field | type | description |", "| --- | --- | --- |"]
    dictionary += [f"| `{n}` | {t} | {d} |" for n, t, d in KB_FIELDS]
    dictionary += [
        "",
        "## Files",
        "- `corpus.jsonl` — one JSON record per line (list fields preserved); use this for retrieval/RAG.",
        "- `corpus.csv` — same records, list fields `;`-joined, for spreadsheets/BI.",
        "- `corpus.parquet` — columnar copy for pandas (best-effort).",
        "- `summary/` — precomputed aggregations (by country, venue, language, year, concept).",
        "",
        "Ask questions over this base with: `nutev ask --project-root <root> \"your question\"`.",
        "",
    ]
    dict_path = kb_dir / "data_dictionary.md"
    dict_path.write_text("\n".join(dictionary), encoding="utf-8")
    paths["data_dictionary"] = dict_path

    return paths


def load_kb_records_from_metadata_csv(path: Path) -> list[dict]:
    """Rebuild KB records from a previously written metadata_master.csv."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return to_kb_records(rows)
